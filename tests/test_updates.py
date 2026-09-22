import pytest

from fund_workbench.samples import sample_updates
from fund_workbench.updates import compare_updates, comparison_to_markdown, parse_update


def test_update_comparison_calculates_metric_deltas() -> None:
    previous, current = sample_updates()
    result = compare_updates(previous, current)
    arr = next(delta for delta in result.deltas if delta.name == "ARR")
    assert arr.absolute_change == 3
    assert arr.percentage_change == 20
    assert result.new_risks == ["Hardware supplier delay threatens September deployments"]
    assert len(result.follow_ups) == 3


def test_text_update_parser_extracts_sections_and_metrics() -> None:
    update = parse_update(
        "Example",
        "August 2026",
        """Metrics
ARR: 25
Retention: 98%

Wins
- Closed an annual contract
Risks
- Hiring is delayed
Asks
- CFO introductions""",
    )
    assert {metric.name for metric in update.metrics} == {"ARR", "Retention"}
    assert update.wins == ["Closed an annual contract"]
    assert update.risks == ["Hiring is delayed"]
    assert update.asks == ["CFO introductions"]


def test_updates_for_different_companies_are_rejected() -> None:
    previous, current = sample_updates()
    current.company = "Another Company"
    with pytest.raises(ValueError, match="same company"):
        compare_updates(previous, current)


def test_comparison_markdown_contains_follow_up_queue() -> None:
    previous, current = sample_updates()
    markdown = comparison_to_markdown(compare_updates(previous, current))
    assert "## Follow-up queue" in markdown
    assert "missing risk is not necessarily resolved" in markdown
