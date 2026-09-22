from __future__ import annotations

import hashlib
import re
from collections import defaultdict

from .models import Claim, EvidenceLedger, EvidenceStatus, Source, SourceType

TOPIC_PATTERNS: dict[str, tuple[str, ...]] = {
    "traction": ("revenue", "arr", "mrr", "customer", "growth", "retention", "orders", "users"),
    "team": ("founder", "team", "hired", "employee", "experience"),
    "product": ("product", "platform", "software", "service", "launch", "build"),
    "market": ("market", "industry", "category", "sector", "tam", "sam", "som"),
    "funding": ("raised", "funding", "round", "investor", "capital"),
    "economics": ("margin", "price", "cost", "cac", "ltv", "burn", "runway"),
    "risk": ("risk", "churn", "delay", "blocked", "decline", "lawsuit", "regulatory"),
}

NUMERIC_PATTERN = re.compile(
    r"(?:[$₹€£]\s*)?\d[\d,.]*(?:\.\d+)?\s*(?:%|x|k|m|b|million|billion|crore|lakh)?",
    re.IGNORECASE,
)
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")


def _claim_id(source_id: str, statement: str) -> str:
    digest = hashlib.sha1(f"{source_id}:{statement}".encode(), usedforsecurity=False).hexdigest()[:10]
    return f"claim-{digest}"


def classify_topic(text: str) -> str:
    lowered = text.lower()
    scores = {topic: sum(term in lowered for term in terms) for topic, terms in TOPIC_PATTERNS.items()}
    topic, score = max(scores.items(), key=lambda item: item[1])
    return topic if score else "general"


def default_status(source_type: SourceType) -> EvidenceStatus:
    if source_type == SourceType.INDEPENDENT:
        return EvidenceStatus.VERIFIED
    if source_type == SourceType.COMPANY:
        return EvidenceStatus.COMPANY_REPORTED
    return EvidenceStatus.REPORTED


def extract_claims_deterministic(sources: list[Source]) -> list[Claim]:
    """Extract checkable statements. This fallback is transparent, not semantic AI."""
    claims: list[Claim] = []
    for source in sources:
        sentences = [part.strip(" -•\t") for part in SENTENCE_PATTERN.split(source.content)]
        candidates = [
            sentence
            for sentence in sentences
            if 20 <= len(sentence) <= 500
            and (NUMERIC_PATTERN.search(sentence) or classify_topic(sentence) != "general")
        ]
        for sentence in candidates[:40]:
            claims.append(
                Claim(
                    id=_claim_id(source.id, sentence),
                    topic=classify_topic(sentence),
                    statement=sentence,
                    status=default_status(source.source_type),
                    source_id=source.id,
                    quote=sentence,
                    confidence=0.55,
                    note="Rule-based extraction; review meaning and context.",
                )
            )
    return claims


def validate_claims(claims: list[Claim], sources: list[Source]) -> list[Claim]:
    """Enforce source integrity after model or deterministic extraction."""
    source_map = {source.id: source for source in sources}
    validated: list[Claim] = []
    seen: set[tuple[str, str]] = set()
    for claim in claims:
        key = ((claim.source_id or ""), claim.statement.lower())
        if key in seen:
            continue
        seen.add(key)
        source = source_map.get(claim.source_id or "")
        if source is None:
            claim.status = EvidenceStatus.INFERRED
            claim.quote = None
            claim.note = "Source reference was missing; treated as an inference."
        elif claim.quote and claim.quote.casefold() not in source.content.casefold():
            claim.status = EvidenceStatus.INFERRED
            claim.quote = None
            claim.note = "Quoted evidence was not found verbatim; treated as an inference."
        elif source.source_type == SourceType.COMPANY and claim.status == EvidenceStatus.VERIFIED:
            claim.status = EvidenceStatus.COMPANY_REPORTED
            claim.note = "Company-supplied evidence cannot independently verify its own claim."
        validated.append(claim)
    return validated


def detect_contradictions(claims: list[Claim]) -> list[str]:
    """Flag differing numeric claims in the same topic for human review."""
    grouped: dict[str, list[Claim]] = defaultdict(list)
    for claim in claims:
        grouped[claim.topic].append(claim)
    contradictions: list[str] = []
    for topic, topic_claims in grouped.items():
        numeric_claims = [claim for claim in topic_claims if NUMERIC_PATTERN.search(claim.statement)]
        values = {
            match.group(0).lower() for claim in numeric_claims for match in NUMERIC_PATTERN.finditer(claim.statement)
        }
        source_ids = {claim.source_id for claim in numeric_claims}
        if len(values) > 1 and len(source_ids) > 1:
            contradictions.append(
                f"{topic.title()}: sources contain different numeric values ({', '.join(sorted(values)[:6])})."
            )
    return contradictions


def build_ledger(company: str, sources: list[Source], ai: bool = False) -> EvidenceLedger:
    if not sources:
        raise ValueError("At least one source is required")
    mode = "deterministic"
    claims: list[Claim]
    if ai:
        from .llm import extract_claims_ai

        claims = extract_claims_ai(sources)
        mode = "ai-assisted"
    else:
        claims = extract_claims_deterministic(sources)
    return EvidenceLedger(
        company=company,
        mode=mode,
        sources=sources,
        claims=validate_claims(claims, sources),
    )
