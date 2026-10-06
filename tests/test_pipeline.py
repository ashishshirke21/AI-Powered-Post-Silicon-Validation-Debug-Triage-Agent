from __future__ import annotations

from app.pipeline.graph import run_pipeline
from app.synthetic.generator import generate_log


def test_end_to_end_pipeline_produces_evidence_backed_report():
    generated = generate_log(scenarios=["thermal_trip", "memory_ecc"], noise_lines=8, seed=7)
    report = run_pipeline("run_test", "synthetic", generated.text)

    assert report.failures, "expected detected failures"
    assert report.hypotheses, "expected hypotheses"
    assert report.experiment_summary

    detected_categories = {f.category for f in report.failures}
    assert "thermal" in detected_categories
    assert "memory" in detected_categories

    # Every surviving hypothesis must cite evidence (no invented root causes).
    for hyp in report.hypotheses:
        assert hyp.evidence_refs

    # Every recommendation must map to a real hypothesis.
    hyp_ids = {h.id for h in report.hypotheses}
    for rec in report.recommendations:
        assert rec.hypothesis_id in hyp_ids


def test_clean_log_yields_no_hypotheses():
    generated = generate_log(scenarios=[], noise_lines=10, seed=11)
    report = run_pipeline("run_clean", "synthetic", generated.text)
    assert report.hypotheses == []
