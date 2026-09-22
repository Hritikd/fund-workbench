from fund_workbench.evidence import build_ledger, detect_contradictions, validate_claims
from fund_workbench.models import Claim, EvidenceStatus, Source, SourceType
from fund_workbench.samples import sample_sources


def test_company_claims_are_not_marked_verified() -> None:
    source = Source(
        id="company",
        title="Company update",
        source_type=SourceType.COMPANY,
        content="The company has 20 paying customers.",
    )
    claim = Claim(
        id="claim-1",
        topic="traction",
        statement="The company has 20 paying customers.",
        status=EvidenceStatus.VERIFIED,
        source_id="company",
        quote="The company has 20 paying customers.",
    )
    result = validate_claims([claim], [source])
    assert result[0].status == EvidenceStatus.COMPANY_REPORTED


def test_non_verbatim_quote_becomes_inference() -> None:
    source = Source(
        id="notes",
        title="Notes",
        source_type=SourceType.CALL_NOTES,
        content="A customer completed a six-week pilot.",
    )
    claim = Claim(
        id="claim-2",
        topic="traction",
        statement="A customer completed a pilot.",
        status=EvidenceStatus.REPORTED,
        source_id="notes",
        quote="Three customers completed pilots.",
    )
    result = validate_claims([claim], [source])
    assert result[0].status == EvidenceStatus.INFERRED
    assert result[0].quote is None


def test_sample_ledger_runs_without_api_key() -> None:
    ledger = build_ledger("Northstar Robotics", sample_sources())
    assert ledger.mode == "deterministic"
    assert len(ledger.claims) >= 6
    assert {claim.topic for claim in ledger.claims} >= {"traction", "team", "risk"}


def test_numeric_differences_across_sources_are_flagged() -> None:
    claims = [
        Claim(
            id="one",
            topic="traction",
            statement="Revenue is 10 million.",
            status=EvidenceStatus.COMPANY_REPORTED,
            source_id="a",
        ),
        Claim(
            id="two",
            topic="traction",
            statement="Revenue is 8 million.",
            status=EvidenceStatus.VERIFIED,
            source_id="b",
        ),
    ]
    assert detect_contradictions(claims)
