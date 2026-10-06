from __future__ import annotations

from app.models.schemas import EvidenceBundle, FailureEvent, LogLine


def build_evidence_bundles(
    failures: list[FailureEvent],
    lines: list[LogLine],
    *,
    context_window: int = 2,
) -> list[EvidenceBundle]:
    """Build one evidence bundle per failure.

    Each bundle includes the matched lines plus ``context_window`` lines before
    and after each match. ``evidence_line_refs`` is the exact set of line IDs the
    LLM is allowed to cite; the guardrail enforces this downstream.
    """
    by_line_no = {line.line_no: line for line in lines}
    ordered_line_nos = sorted(by_line_no)
    index_of = {ln: i for i, ln in enumerate(ordered_line_nos)}

    bundles: list[EvidenceBundle] = []
    for failure in failures:
        evidence_nos: set[int] = set()
        for ref in failure.line_refs:
            if ref not in index_of:
                continue
            center = index_of[ref]
            lo = max(0, center - context_window)
            hi = min(len(ordered_line_nos) - 1, center + context_window)
            for i in range(lo, hi + 1):
                evidence_nos.add(ordered_line_nos[i])

        sorted_nos = sorted(evidence_nos)
        evidence_lines = [by_line_no[n] for n in sorted_nos]
        components = sorted({ln.component for ln in evidence_lines if ln.component})
        evidence_text = "\n".join(f"L{ln.line_no}: {ln.raw}" for ln in evidence_lines)

        bundles.append(
            EvidenceBundle(
                id=f"EV_{failure.id}",
                failure_id=failure.id,
                component=components[0] if components else None,
                evidence_line_refs=sorted_nos,
                evidence_text=evidence_text,
            )
        )

    return bundles
