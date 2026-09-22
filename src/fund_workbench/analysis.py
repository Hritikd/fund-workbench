from __future__ import annotations

import re
from collections import Counter

from .evidence import detect_contradictions
from .models import (
    DiligenceQuestion,
    EvidenceLedger,
    EvidenceStatus,
    ScreeningMemo,
    Thesis,
    ThesisAssessment,
)

CATEGORY_QUESTIONS: dict[str, list[tuple[str, str]]] = {
    "traction": [
        (
            "How is the core traction metric defined, and what is the cohort and period?",
            "Definitions prevent misleading comparisons.",
        ),
        (
            "What share of growth comes from retained customers versus new acquisition?",
            "Growth quality depends on retention and repeatability.",
        ),
    ],
    "economics": [
        (
            "What is contribution margin after the costs required to serve the customer?",
            "Top-line revenue can hide delivery costs.",
        ),
        (
            "How do acquisition cost and payback vary by channel?",
            "Blended acquisition metrics can hide weak channels.",
        ),
    ],
    "market": [
        (
            "Which customer segment feels the problem most acutely, and what do they use today?",
            "A bottom-up wedge is more testable than a broad market claim.",
        ),
        (
            "What evidence would disprove the current market-sizing assumption?",
            "Falsifiability improves market judgment.",
        ),
    ],
    "product": [
        (
            "What user action demonstrates recurring value rather than initial curiosity?",
            "Usage needs a meaningful activation and retention definition.",
        ),
        (
            "What breaks when the product moves from ten customers to one hundred?",
            "Early product success may depend on manual operations.",
        ),
    ],
    "team": [
        (
            "Which critical capability is missing from the current team?",
            "Execution risk often concentrates in an uncovered function.",
        ),
        (
            "What evidence caused the founders to change an important view?",
            "Learning speed is more observable than confidence.",
        ),
    ],
    "funding": [
        (
            "What milestones will this round finance, and what evidence will each milestone create?",
            "A funding plan should connect capital to de-risking.",
        ),
        (
            "What are the current ownership, option-pool, and financing constraints?",
            "Capital structure affects future flexibility.",
        ),
    ],
    "risk": [
        (
            "Who owns the largest current risk, and what is the next dated action?",
            "Risks need owners and resolution paths.",
        ),
        (
            "What regulatory, security, or dependency failure could stop deployment?",
            "External constraints can dominate product quality.",
        ),
    ],
}


def _corpus(ledger: EvidenceLedger) -> str:
    return " ".join(claim.statement.lower() for claim in ledger.claims)


def assess_thesis(ledger: EvidenceLedger, thesis: Thesis) -> ThesisAssessment:
    corpus = _corpus(ledger)

    def matches(terms: list[str]) -> list[str]:
        return [term for term in terms if term.lower() in corpus]

    matched_required = matches(thesis.required_terms)
    missing_required = [term for term in thesis.required_terms if term not in matched_required]
    matched_preferred = matches(thesis.preferred_terms)
    exclusions = matches(thesis.excluded_terms)

    required_score = 60 * len(matched_required) / max(1, len(thesis.required_terms))
    preferred_score = 30 * len(matched_preferred) / max(1, len(thesis.preferred_terms))
    evidence_bonus = min(10, len(ledger.claims) // 3)
    score = max(0, min(100, round(required_score + preferred_score + evidence_bonus - 25 * len(exclusions))))
    return ThesisAssessment(
        score=score,
        matched_required=matched_required,
        missing_required=missing_required,
        matched_preferred=matched_preferred,
        exclusions_found=exclusions,
        explanation=(
            "Keyword-based triage score for routing, not an investment score. "
            "A reviewer must confirm meaning, context, and source quality."
        ),
    )


def generate_diligence_questions(ledger: EvidenceLedger, limit: int = 10) -> list[DiligenceQuestion]:
    topics = Counter(claim.topic for claim in ledger.claims)
    unknown_topics = [topic for topic in CATEGORY_QUESTIONS if topics[topic] == 0]
    questions: list[DiligenceQuestion] = []
    for topic in unknown_topics:
        question, reason = CATEGORY_QUESTIONS[topic][0]
        questions.append(DiligenceQuestion(category=topic, question=question, reason=reason, priority="high"))
    for contradiction in detect_contradictions(ledger.claims):
        topic = contradiction.split(":", 1)[0].lower()
        questions.append(
            DiligenceQuestion(
                category=topic,
                question=f"Which source and definition should govern the conflicting {topic} values?",
                reason=contradiction,
                priority="high",
            )
        )
    for topic, _count in topics.most_common():
        if topic in CATEGORY_QUESTIONS:
            for question, reason in CATEGORY_QUESTIONS[topic]:
                questions.append(DiligenceQuestion(category=topic, question=question, reason=reason, priority="medium"))
    unique: list[DiligenceQuestion] = []
    seen: set[str] = set()
    for question in questions:
        if question.question not in seen:
            seen.add(question.question)
            unique.append(question)
    return unique[:limit]


def build_screening_memo(ledger: EvidenceLedger, thesis: Thesis) -> ScreeningMemo:
    verified = [
        claim.statement
        for claim in ledger.claims
        if claim.status in {EvidenceStatus.VERIFIED, EvidenceStatus.COMPANY_REPORTED, EvidenceStatus.REPORTED}
    ]
    risks = [
        claim.statement
        for claim in ledger.claims
        if claim.topic == "risk" or claim.status in {EvidenceStatus.UNKNOWN, EvidenceStatus.INFERRED}
    ]
    contradictions = detect_contradictions(ledger.claims)
    assessment = assess_thesis(ledger, thesis)
    summary = (
        f"{ledger.company} has {len(ledger.claims)} extracted claims across {len(ledger.sources)} sources. "
        f"{len(verified)} claims retain attributable evidence; {len(risks)} items require explicit review."
    )
    return ScreeningMemo(
        company=ledger.company,
        thesis=assessment,
        summary=summary,
        supported_points=verified[:8],
        risks_and_unknowns=risks[:8]
        + [f"Missing required thesis term: {term}" for term in assessment.missing_required],
        contradictions=contradictions,
        next_questions=generate_diligence_questions(ledger),
    )


def memo_to_markdown(memo: ScreeningMemo) -> str:
    def bullets(items: list[str]) -> str:
        return "\n".join(f"- {item}" for item in items) or "- None recorded"

    questions = "\n".join(
        f"{index}. **[{question.priority.upper()}] {question.category.title()}** — {question.question}  \n"
        f"   _Why: {question.reason}_"
        for index, question in enumerate(memo.next_questions, 1)
    )
    return f"""# Screening brief: {memo.company}

Generated: {memo.generated_at.isoformat()}

## Summary

{memo.summary}

## Thesis triage

- Routing score: **{memo.thesis.score}/100**
- Matched required: {", ".join(memo.thesis.matched_required) or "None"}
- Missing required: {", ".join(memo.thesis.missing_required) or "None"}
- Matched preferred: {", ".join(memo.thesis.matched_preferred) or "None"}
- Exclusions found: {", ".join(memo.thesis.exclusions_found) or "None"}

_{memo.thesis.explanation}_

## Supported or attributable points

{bullets(memo.supported_points)}

## Risks and unknowns

{bullets(memo.risks_and_unknowns)}

## Possible contradictions

{bullets(memo.contradictions)}

## Next diligence questions

{questions or "No questions generated."}

## Decision

{memo.decision}
"""


METRIC_PATTERN = re.compile(
    r"^\s*(?:[-*]\s*)?(?P<name>[A-Za-z][A-Za-z0-9 /_-]{1,60})\s*:\s*"
    r"(?P<prefix>[$₹€£]?)\s*(?P<value>-?[\d,.]+)\s*(?P<unit>%|x|k|m|b|crore|lakh)?\s*$",
    re.IGNORECASE,
)


def parse_metric_lines(text: str) -> dict[str, tuple[float, str]]:
    metrics: dict[str, tuple[float, str]] = {}
    for line in text.splitlines():
        match = METRIC_PATTERN.match(line)
        if not match:
            continue
        value = float(match.group("value").replace(",", ""))
        prefix = match.group("prefix")
        unit = match.group("unit") or "number"
        if prefix:
            unit = prefix
        metrics[match.group("name").strip()] = (value, unit.lower())
    return metrics
