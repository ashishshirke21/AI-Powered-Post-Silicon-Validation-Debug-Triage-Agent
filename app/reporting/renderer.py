from __future__ import annotations

from app.models.schemas import LogLine, TriageReport
from app.parsing.parser import parse_log


def render_markdown(report: TriageReport, raw_log: str | None = None) -> str:
    """Render a human-readable, evidence-traceable Markdown report.

    When ``raw_log`` is provided, cited evidence lines are quoted inline so every
    hypothesis can be traced back to the exact log text that produced it.
    """
    lines_by_no: dict[int, LogLine] = {}
    if raw_log:
        lines_by_no = {ln.line_no: ln for ln in parse_log(raw_log)}

    out: list[str] = []
    out.append(f"# Triage Report — Run `{report.run_id}`")
    out.append("")
    out.append(f"- **Source:** {report.source}")
    out.append(f"- **Generated:** {report.created_at.isoformat(timespec='seconds')}")
    out.append("")
    out.append("## Experiment Summary")
    out.append(report.experiment_summary or "_No summary available._")
    out.append("")

    out.append("## Detected Failures")
    if not report.failures:
        out.append("_No failures detected._")
    for failure in report.failures:
        refs = ", ".join(f"L{n}" for n in failure.line_refs)
        out.append(
            f"- **{failure.summary}** "
            f"(`{failure.signature_id}`, {failure.severity.value}) — evidence: {refs}"
        )
    out.append("")

    out.append("## Root-Cause Hypotheses")
    if not report.hypotheses:
        out.append("_No evidence-backed hypotheses were generated._")
    for hyp in report.hypotheses:
        out.append(f"### {hyp.id} (confidence {hyp.confidence:.2f})")
        out.append(
            f"_Blended from LLM self-confidence {hyp.llm_confidence:.2f} + "
            f"signature severity weighting._"
        )
        out.append(hyp.statement)
        if hyp.flagged:
            out.append(f"> ⚠️ Flagged: {hyp.flag_reason}")
        out.append("")
        out.append("**Cited evidence:**")
        if not hyp.evidence_refs:
            out.append("- _None_")
        for ref in hyp.evidence_refs:
            line = lines_by_no.get(ref)
            quote = f": `{line.raw}`" if line else ""
            out.append(f"- L{ref}{quote}")
        out.append("")

    out.append("## Recommended Next Steps")
    if not report.recommendations:
        out.append("_No recommendations._")
    for rec in report.recommendations:
        out.append(f"- **{rec.action}** (for `{rec.hypothesis_id}`) — {rec.rationale}")
    out.append("")

    return "\n".join(out)
