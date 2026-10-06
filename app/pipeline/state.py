from __future__ import annotations

from typing import TypedDict

from app.llm.provider import TriageLLM
from app.models.schemas import (
    EvidenceBundle,
    FailureEvent,
    Hypothesis,
    LogLine,
    Recommendation,
)


class PipelineState(TypedDict, total=False):
    # Inputs
    run_id: str
    source: str
    raw_log: str
    llm: TriageLLM | None
    min_confidence: float
    llm_weight: float

    # Produced by nodes, in order.
    lines: list[LogLine]
    failures: list[FailureEvent]
    bundles: list[EvidenceBundle]
    hypotheses: list[Hypothesis]
    recommendations: list[Recommendation]
    experiment_summary: str
