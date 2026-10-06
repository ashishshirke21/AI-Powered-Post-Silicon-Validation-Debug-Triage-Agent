from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Severity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class RunStatus(StrEnum):
    CREATED = "created"
    PARSED = "parsed"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    FAILED = "failed"


class LogLine(BaseModel):
    """A single parsed log line. ``line_no`` is the stable evidence ID."""

    line_no: int
    raw: str
    timestamp: datetime | None = None
    severity: Severity = Severity.INFO
    component: str | None = None
    message: str = ""


class Signature(BaseModel):
    """A deterministic failure signature loaded from the catalog."""

    id: str
    name: str
    category: str
    pattern: str
    severity: Severity
    description: str = ""


class FailureEvent(BaseModel):
    """A detected failure, tracing back to the log lines that triggered it."""

    id: str
    signature_id: str
    category: str
    severity: Severity
    summary: str
    line_refs: list[int] = Field(default_factory=list)


class EvidenceBundle(BaseModel):
    """Failure plus surrounding context lines handed to the LLM for triage."""

    id: str
    failure_id: str
    component: str | None = None
    # Evidence line IDs available to the LLM. Hypotheses may only cite these.
    evidence_line_refs: list[int] = Field(default_factory=list)
    evidence_text: str = ""


class Hypothesis(BaseModel):
    """An AI-generated root-cause hypothesis grounded in cited evidence."""

    id: str
    failure_id: str
    statement: str
    category: str = "unknown"
    # Final score: LLM self-assessment blended with signature severity weighting.
    confidence: float = 0.0
    # Raw LLM self-reported confidence, kept for transparency.
    llm_confidence: float = 0.0
    evidence_refs: list[int] = Field(default_factory=list)
    # Set by the guardrail when cited evidence cannot be verified.
    flagged: bool = False
    flag_reason: str | None = None


class Recommendation(BaseModel):
    """A suggested next diagnostic step tied to a hypothesis."""

    id: str
    hypothesis_id: str
    action: str
    rationale: str = ""


class TriageReport(BaseModel):
    """The assembled, traceable output of a run."""

    run_id: str
    created_at: datetime
    source: str
    experiment_summary: str = ""
    failures: list[FailureEvent] = Field(default_factory=list)
    hypotheses: list[Hypothesis] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)


class Run(BaseModel):
    id: str
    created_at: datetime
    source: str
    status: RunStatus = RunStatus.CREATED
    filename: str | None = None
    line_count: int = 0
