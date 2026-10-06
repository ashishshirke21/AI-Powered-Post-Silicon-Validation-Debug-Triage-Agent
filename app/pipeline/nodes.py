from __future__ import annotations

from app.correlation.correlator import build_evidence_bundles
from app.detection.matcher import detect_failures
from app.parsing.parser import parse_log
from app.pipeline.state import PipelineState
from app.triage.runner import triage_failure


def parse_node(state: PipelineState) -> PipelineState:
    lines = parse_log(state.get("raw_log", ""))
    return {"lines": lines}


def detect_node(state: PipelineState) -> PipelineState:
    failures = detect_failures(state.get("lines", []))
    return {"failures": failures}


def correlate_node(state: PipelineState) -> PipelineState:
    bundles = build_evidence_bundles(state.get("failures", []), state.get("lines", []))
    return {"bundles": bundles}


def triage_node(state: PipelineState) -> PipelineState:
    failures = state.get("failures", [])
    bundles_by_failure = {b.failure_id: b for b in state.get("bundles", [])}
    llm = state.get("llm")
    min_conf = state.get("min_confidence", 0.0)
    llm_weight = state.get("llm_weight", 0.6)

    all_hyps = []
    all_recs = []
    for failure in failures:
        bundle = bundles_by_failure.get(failure.id)
        if bundle is None:
            continue
        hyps, recs = triage_failure(
            failure, bundle, llm=llm, min_confidence=min_conf, llm_weight=llm_weight
        )
        all_hyps.extend(hyps)
        all_recs.extend(recs)

    return {"hypotheses": all_hyps, "recommendations": all_recs}


def summary_node(state: PipelineState) -> PipelineState:
    failures = state.get("failures", [])
    hypotheses = state.get("hypotheses", [])
    lines = state.get("lines", [])

    if not failures:
        summary = (
            f"Parsed {len(lines)} log line(s). No known failure signatures matched; "
            f"no root-cause hypotheses generated."
        )
    else:
        categories = sorted({f.category for f in failures})
        summary = (
            f"Parsed {len(lines)} log line(s). Detected {len(failures)} failure(s) "
            f"across: {', '.join(categories)}. Generated {len(hypotheses)} "
            f"evidence-backed hypothesis(es)."
        )
    return {"experiment_summary": summary}
