from __future__ import annotations

from .models import MetricValue, PortfolioUpdate, Source, SourceType, Thesis


def sample_sources() -> list[Source]:
    return [
        Source(
            id="company-update",
            title="Northstar Robotics company update",
            source_type=SourceType.COMPANY,
            content=(
                "Northstar Robotics builds vision-guided quality inspection for small manufacturers. "
                "The company reports 14 paying factories and ₹18 lakh ARR as of August 2026. "
                "Monthly customer retention is 96%. The two founders previously worked in industrial automation. "
                "The company is raising a ₹3 crore seed round to hire engineering and sales staff. "
                "A delayed hardware supplier remains the largest deployment risk."
            ),
            url="https://example.com/company-update",
        ),
        Source(
            id="customer-notes",
            title="Reference call notes",
            source_type=SourceType.CALL_NOTES,
            content=(
                "A plant manager said Northstar reduced manual inspection time during a six-week pilot. "
                "The manager has not approved a plant-wide rollout. Integration took nine working days. "
                "The buyer expects a formal security review before renewal."
            ),
        ),
        Source(
            id="independent-brief",
            title="Industry association brief",
            source_type=SourceType.INDEPENDENT,
            content=(
                "Small manufacturers increasingly evaluate machine-vision inspection, but integration and "
                "operator training remain common adoption barriers. The brief does not estimate market size."
            ),
            url="https://example.com/industry-brief",
        ),
    ]


def sample_thesis() -> Thesis:
    return Thesis(
        name="Early industrial software",
        required_terms=["manufacturer", "paying"],
        preferred_terms=["retention", "automation", "inspection"],
        excluded_terms=["gambling"],
        questions=["Can deployment become repeatable without services-heavy work?"],
    )


def sample_updates() -> tuple[PortfolioUpdate, PortfolioUpdate]:
    previous = PortfolioUpdate(
        company="Northstar Robotics",
        period="July 2026",
        metrics=[
            MetricValue(name="ARR", value=15, unit="₹ lakh"),
            MetricValue(name="Paying factories", value=12),
            MetricValue(name="Monthly retention", value=95, unit="%"),
        ],
        wins=["Completed first automotive pilot"],
        risks=["Security review is delaying one expansion"],
        asks=["Introductions to two automotive suppliers"],
    )
    current = PortfolioUpdate(
        company="Northstar Robotics",
        period="August 2026",
        metrics=[
            MetricValue(name="ARR", value=18, unit="₹ lakh"),
            MetricValue(name="Paying factories", value=14),
            MetricValue(name="Monthly retention", value=96, unit="%"),
        ],
        wins=["Converted two pilots to annual contracts"],
        risks=["Hardware supplier delay threatens September deployments"],
        asks=["Backup hardware supplier introductions", "Security review template"],
    )
    return previous, current
