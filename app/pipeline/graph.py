from __future__ import annotations

from datetime import datetime
from functools import lru_cache

from langgraph.graph import END, START, StateGraph

from app.llm.provider import TriageLLM
from app.models.schemas import TriageReport
from app.pipeline.nodes import (
    correlate_node,
    detect_node,
    parse_node,
    summary_node,
    triage_node,
)
from app.pipeline.state import PipelineState


@lru_cache
def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("parse", parse_node)
    graph.add_node("detect", detect_node)
    graph.add_node("correlate", correlate_node)
    graph.add_node("triage", triage_node)
    graph.add_node("summarize", summary_node)

    graph.add_edge(START, "parse")
    graph.add_edge("parse", "detect")
    graph.add_edge("detect", "correlate")
    graph.add_edge("correlate", "triage")
    graph.add_edge("triage", "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()


def run_pipeline(
    run_id: str,
    source: str,
    raw_log: str,
    *,
    llm: TriageLLM | None = None,
    min_confidence: float = 0.0,
    llm_weight: float = 0.6,
) -> TriageReport:
    """Execute the full deterministic triage pipeline and assemble the report."""
    app = build_graph()
    initial: PipelineState = {
        "run_id": run_id,
        "source": source,
        "raw_log": raw_log,
        "llm": llm,
        "min_confidence": min_confidence,
        "llm_weight": llm_weight,
    }
    final: PipelineState = app.invoke(initial)

    return TriageReport(
        run_id=run_id,
        created_at=datetime.now(),
        source=source,
        experiment_summary=final.get("experiment_summary", ""),
        failures=final.get("failures", []),
        hypotheses=final.get("hypotheses", []),
        recommendations=final.get("recommendations", []),
    )
