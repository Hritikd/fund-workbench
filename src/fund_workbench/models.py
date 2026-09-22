from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SourceType(str, Enum):
    COMPANY = "company"
    INDEPENDENT = "independent"
    CALL_NOTES = "call_notes"
    INTERNAL = "internal"


class EvidenceStatus(str, Enum):
    VERIFIED = "verified"
    COMPANY_REPORTED = "company_reported"
    REPORTED = "reported"
    INFERRED = "inferred"
    UNKNOWN = "unknown"
    CONTRADICTED = "contradicted"


class Source(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str = Field(min_length=1, max_length=80)
    title: str = Field(min_length=1, max_length=200)
    source_type: SourceType
    content: str = Field(min_length=1)
    url: str | None = None

    @field_validator("id")
    @classmethod
    def safe_id(cls, value: str) -> str:
        cleaned = "-".join(value.lower().split())
        allowed = "".join(ch for ch in cleaned if ch.isalnum() or ch in "-_")
        if not allowed:
            raise ValueError("source id must contain letters or numbers")
        return allowed


class Claim(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    id: str
    topic: str
    statement: str
    status: EvidenceStatus
    source_id: str | None = None
    quote: str | None = None
    confidence: float = Field(default=0.6, ge=0, le=1)
    note: str | None = None


class ClaimExtraction(BaseModel):
    claims: list[Claim]


class EvidenceLedger(BaseModel):
    company: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    mode: str = "deterministic"
    sources: list[Source]
    claims: list[Claim]


class Thesis(BaseModel):
    name: str
    required_terms: list[str] = Field(default_factory=list)
    preferred_terms: list[str] = Field(default_factory=list)
    excluded_terms: list[str] = Field(default_factory=list)
    questions: list[str] = Field(default_factory=list)


class ThesisAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    matched_required: list[str]
    missing_required: list[str]
    matched_preferred: list[str]
    exclusions_found: list[str]
    explanation: str


class DiligenceQuestion(BaseModel):
    category: str
    question: str
    reason: str
    priority: str = Field(pattern="^(high|medium|low)$")


class ScreeningMemo(BaseModel):
    company: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    thesis: ThesisAssessment
    summary: str
    supported_points: list[str]
    risks_and_unknowns: list[str]
    contradictions: list[str]
    next_questions: list[DiligenceQuestion]
    decision: str = "Needs human review"


class MetricValue(BaseModel):
    name: str
    value: float
    unit: str = "number"


class PortfolioUpdate(BaseModel):
    company: str
    period: str
    metrics: list[MetricValue] = Field(default_factory=list)
    wins: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    asks: list[str] = Field(default_factory=list)


class MetricDelta(BaseModel):
    name: str
    previous: float | None
    current: float | None
    unit: str
    absolute_change: float | None
    percentage_change: float | None


class UpdateComparison(BaseModel):
    company: str
    previous_period: str
    current_period: str
    deltas: list[MetricDelta]
    new_risks: list[str]
    resolved_risks: list[str]
    current_asks: list[str]
    follow_ups: list[str]
