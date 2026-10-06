from __future__ import annotations

from app.llm.provider import TriageLLM, get_llm
from app.models.schemas import (
    EvidenceBundle,
    FailureEvent,
    Hypothesis,
    Recommendation,
)
from app.triage.guardrails import validate_hypotheses
from app.triage.prompts import build_triage_prompt
from app.triage.scoring import blend_confidence


def _coerce_hypotheses(raw: list[dict], failure_id: str) -> list[Hypothesis]:
    hypotheses: list[Hypothesis] = []
    for item in raw:
        try:
            llm_conf = float(item.get("confidence", 0.0))
            hypotheses.append(
                Hypothesis(
                    id=item.get("id", f"HYP_{failure_id}"),
                    failure_id=item.get("failure_id", failure_id),
                    statement=item.get("statement", ""),
                    category=item.get("category", "unknown"),
                    confidence=llm_conf,
                    llm_confidence=llm_conf,
                    evidence_refs=[int(x) for x in item.get("evidence_refs", [])],
                )
            )
        except (TypeError, ValueError):
            continue
    return hypotheses


def _coerce_recommendations(
    raw: list[dict], kept_hyp_ids: set[str]
) -> list[Recommendation]:
    recs: list[Recommendation] = []
    for item in raw:
        hyp_id = item.get("hypothesis_id", "")
        # Only keep recommendations tied to a surviving (evidence-backed) hypothesis.
        if hyp_id not in kept_hyp_ids:
            continue
        recs.append(
            Recommendation(
                id=item.get("id", f"REC_{hyp_id}"),
                hypothesis_id=hyp_id,
                action=item.get("action", ""),
                rationale=item.get("rationale", ""),
            )
        )
    return recs


def triage_failure(
    failure: FailureEvent,
    bundle: EvidenceBundle,
    *,
    llm: TriageLLM | None = None,
    min_confidence: float = 0.0,
    llm_weight: float = 0.6,
) -> tuple[list[Hypothesis], list[Recommendation]]:
    """Run the LLM on one failure and enforce evidence grounding on its output."""
    client = llm or get_llm()
    prompt = build_triage_prompt(failure, bundle)
    result = client.triage(prompt)

    raw_hyps = result.get("hypotheses", []) if isinstance(result, dict) else []
    raw_recs = result.get("recommendations", []) if isinstance(result, dict) else []

    hypotheses = _coerce_hypotheses(raw_hyps, failure.id)
    # Blend the LLM's self-confidence with this failure's severity weight.
    for hyp in hypotheses:
        hyp.confidence = blend_confidence(
            hyp.llm_confidence, failure.severity, llm_weight=llm_weight
        )
    hypotheses = validate_hypotheses(hypotheses, bundle, min_confidence=min_confidence)

    kept_ids = {h.id for h in hypotheses}
    recommendations = _coerce_recommendations(raw_recs, kept_ids)
    return hypotheses, recommendations
