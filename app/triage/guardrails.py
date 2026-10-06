from __future__ import annotations

from app.models.schemas import EvidenceBundle, Hypothesis

# This module is the core enforcement of the "assisted, not inventive" principle.
# Any hypothesis that cites evidence not present in its bundle is rejected or
# flagged so the AI can never fabricate a root cause out of thin air.


def validate_hypotheses(
    hypotheses: list[Hypothesis],
    bundle: EvidenceBundle,
    *,
    min_confidence: float = 0.0,
    drop_unflagged: bool = True,
) -> list[Hypothesis]:
    """Enforce evidence grounding on LLM-produced hypotheses.

    A hypothesis is valid only if it cites at least one line ID and every cited
    ID exists in ``bundle.evidence_line_refs``. Invalid ones are flagged; if
    ``drop_unflagged`` is True they are removed from the returned list.
    Hypotheses below ``min_confidence`` are also dropped.
    """
    allowed = set(bundle.evidence_line_refs)
    kept: list[Hypothesis] = []

    for hyp in hypotheses:
        cited = set(hyp.evidence_refs)
        invalid = cited - allowed

        if not cited:
            hyp.flagged = True
            hyp.flag_reason = "No evidence cited; cannot ground this hypothesis."
        elif invalid:
            hyp.flagged = True
            hyp.flag_reason = (
                f"Cited evidence not present in bundle: {sorted(invalid)}"
            )
            # Keep only the verifiable references.
            hyp.evidence_refs = sorted(cited & allowed)

        if hyp.flagged and drop_unflagged:
            continue
        if hyp.confidence < min_confidence:
            continue
        kept.append(hyp)

    return kept
