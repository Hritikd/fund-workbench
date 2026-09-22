from fund_workbench.analysis import assess_thesis, build_screening_memo, memo_to_markdown
from fund_workbench.evidence import build_ledger
from fund_workbench.samples import sample_sources, sample_thesis


def test_thesis_score_exposes_matches_and_missing_terms() -> None:
    ledger = build_ledger("Northstar Robotics", sample_sources())
    result = assess_thesis(ledger, sample_thesis())
    assert 0 <= result.score <= 100
    assert "manufacturer" in result.matched_required
    assert "gambling" not in result.exclusions_found
    assert "not an investment score" in result.explanation


def test_memo_is_reviewable_and_exportable() -> None:
    ledger = build_ledger("Northstar Robotics", sample_sources())
    memo = build_screening_memo(ledger, sample_thesis())
    markdown = memo_to_markdown(memo)
    assert "# Screening brief: Northstar Robotics" in markdown
    assert "## Next diligence questions" in markdown
    assert memo.decision == "Needs human review"
    assert memo.next_questions
