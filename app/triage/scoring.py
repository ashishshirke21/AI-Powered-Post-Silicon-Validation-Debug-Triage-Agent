from __future__ import annotations

from app.models.schemas import Severity

# Higher-severity failures carry more diagnostic weight, so a hypothesis about a
# CRITICAL failure is scored higher than the same LLM confidence on a WARNING.
SEVERITY_WEIGHTS: dict[Severity, float] = {
    Severity.CRITICAL: 1.0,
    Severity.ERROR: 0.75,
    Severity.WARNING: 0.5,
    Severity.INFO: 0.25,
}


def blend_confidence(
    llm_confidence: float, severity: Severity, *, llm_weight: float = 0.6
) -> float:
    """Blend LLM self-confidence with signature severity weighting.

    ``llm_weight`` controls how much the LLM's own estimate counts; the
    remainder is the severity weight. Result is clamped to [0.0, 1.0].
    """
    llm_weight = min(max(llm_weight, 0.0), 1.0)
    sev_weight = SEVERITY_WEIGHTS.get(severity, 0.5)
    llm_conf = min(max(llm_confidence, 0.0), 1.0)
    blended = llm_weight * llm_conf + (1.0 - llm_weight) * sev_weight
    return round(min(max(blended, 0.0), 1.0), 4)
