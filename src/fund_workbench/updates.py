from __future__ import annotations

import re

from .analysis import parse_metric_lines
from .models import MetricDelta, MetricValue, PortfolioUpdate, UpdateComparison

SECTION_PATTERN = re.compile(r"^\s*(wins?|risks?|blockers?|asks?|help needed)\s*:?\s*$", re.IGNORECASE)


def parse_update(company: str, period: str, text: str) -> PortfolioUpdate:
    """Parse a lightweight text update with Metrics, Wins, Risks, and Asks sections."""
    metrics = [
        MetricValue(name=name, value=value, unit=unit) for name, (value, unit) in parse_metric_lines(text).items()
    ]
    sections: dict[str, list[str]] = {"wins": [], "risks": [], "asks": []}
    active: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        heading = SECTION_PATTERN.match(line)
        if heading:
            label = heading.group(1).lower()
            if label.startswith("win"):
                active = "wins"
            elif label.startswith(("risk", "block")):
                active = "risks"
            else:
                active = "asks"
            continue
        if active and line.startswith(("-", "*", "•")):
            item = line.lstrip("-*• ").strip()
            if item:
                sections[active].append(item)
    return PortfolioUpdate(company=company, period=period, metrics=metrics, **sections)


def compare_updates(previous: PortfolioUpdate, current: PortfolioUpdate) -> UpdateComparison:
    if previous.company.casefold() != current.company.casefold():
        raise ValueError("Updates must refer to the same company")
    previous_metrics = {metric.name.casefold(): metric for metric in previous.metrics}
    current_metrics = {metric.name.casefold(): metric for metric in current.metrics}
    deltas: list[MetricDelta] = []
    for key in sorted(previous_metrics.keys() | current_metrics.keys()):
        old = previous_metrics.get(key)
        new = current_metrics.get(key)
        old_value = old.value if old else None
        new_value = new.value if new else None
        absolute = new_value - old_value if old_value is not None and new_value is not None else None
        percentage = None
        if absolute is not None and old_value not in {None, 0}:
            percentage = absolute / old_value * 100
        deltas.append(
            MetricDelta(
                name=(new or old).name,
                previous=old_value,
                current=new_value,
                unit=(new or old).unit,
                absolute_change=absolute,
                percentage_change=percentage,
            )
        )

    previous_risks = {risk.casefold(): risk for risk in previous.risks}
    current_risks = {risk.casefold(): risk for risk in current.risks}
    new_risks = [current_risks[key] for key in current_risks.keys() - previous_risks.keys()]
    resolved = [previous_risks[key] for key in previous_risks.keys() - current_risks.keys()]
    follow_ups = [f"Assign an owner and date for: {risk}" for risk in new_risks]
    follow_ups.extend(f"Respond to company ask: {ask}" for ask in current.asks)
    return UpdateComparison(
        company=current.company,
        previous_period=previous.period,
        current_period=current.period,
        deltas=deltas,
        new_risks=new_risks,
        resolved_risks=resolved,
        current_asks=current.asks,
        follow_ups=follow_ups,
    )


def comparison_to_markdown(comparison: UpdateComparison) -> str:
    metric_rows = []
    for delta in comparison.deltas:
        pct = "n.a." if delta.percentage_change is None else f"{delta.percentage_change:+.1f}%"
        metric_rows.append(
            f"| {delta.name} | {delta.previous if delta.previous is not None else 'n.a.'} | "
            f"{delta.current if delta.current is not None else 'n.a.'} | {delta.unit} | {pct} |"
        )

    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) or "- None recorded"

    return f"""# Portfolio update comparison: {comparison.company}

{comparison.previous_period} → {comparison.current_period}

## Metrics

| Metric | Previous | Current | Unit | Change |
|---|---:|---:|---|---:|
{chr(10).join(metric_rows)}

## New risks

{bullets(comparison.new_risks)}

## Risks no longer reported

{bullets(comparison.resolved_risks)}

_A missing risk is not necessarily resolved. Confirm with the company._

## Current asks

{bullets(comparison.current_asks)}

## Follow-up queue

{bullets(comparison.follow_ups)}
"""
