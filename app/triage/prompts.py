from __future__ import annotations

from app.models.schemas import EvidenceBundle, FailureEvent

SYSTEM_RULES = """You are a post-silicon validation triage assistant. You do NOT guess.
Rules:
- Only propose root-cause hypotheses supported by the EVIDENCE lines provided.
- Every hypothesis MUST cite one or more evidence line IDs (the integer after 'L').
- Never cite a line ID that is not present in the EVIDENCE block.
- If evidence is insufficient, say so and give low confidence.
- confidence is a float between 0.0 and 1.0.
Return ONLY a JSON object with this shape:
{
  "hypotheses": [
    {"id": "HYP_...", "failure_id": "...", "statement": "...",
     "category": "...", "confidence": 0.0, "evidence_refs": [12, 13]}
  ],
  "recommendations": [
    {"id": "REC_...", "hypothesis_id": "HYP_...", "action": "...", "rationale": "..."}
  ]
}"""


def build_triage_prompt(failure: FailureEvent, bundle: EvidenceBundle) -> str:
    valid_ids = ", ".join(str(n) for n in bundle.evidence_line_refs)
    return (
        f"{SYSTEM_RULES}\n\n"
        f"FAILURE_ID: {failure.id}\n"
        f"CATEGORY: {failure.category}\n"
        f"SEVERITY: {failure.severity.value}\n"
        f"DETECTED_SUMMARY: {failure.summary}\n\n"
        f"VALID_EVIDENCE_IDS: [{valid_ids}]\n"
        f"EVIDENCE:\n{bundle.evidence_text}\n\n"
        f"Produce the JSON now."
    )
