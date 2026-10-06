from __future__ import annotations

from app.correlation.correlator import build_evidence_bundles
from app.detection.matcher import detect_failures
from app.models.schemas import EvidenceBundle, Hypothesis
from app.parsing.parser import parse_log
from app.synthetic.generator import generate_log
from app.triage.guardrails import validate_hypotheses


def _bundle_with_refs(refs: list[int]) -> EvidenceBundle:
    return EvidenceBundle(
        id="EV_X",
        failure_id="FAIL_X",
        evidence_line_refs=refs,
        evidence_text="\n".join(f"L{n}: sample" for n in refs),
    )


def test_hypothesis_citing_fabricated_evidence_is_dropped():
    bundle = _bundle_with_refs([10, 11, 12])
    fabricated = Hypothesis(
        id="HYP_X",
        failure_id="FAIL_X",
        statement="Invented cause.",
        confidence=0.9,
        evidence_refs=[999],  # not in the bundle
    )
    kept = validate_hypotheses([fabricated], bundle, drop_unflagged=True)
    assert kept == []


def test_hypothesis_without_any_citation_is_dropped():
    bundle = _bundle_with_refs([1, 2, 3])
    uncited = Hypothesis(
        id="HYP_Y", failure_id="FAIL_X", statement="No evidence.", confidence=0.8
    )
    kept = validate_hypotheses([uncited], bundle, drop_unflagged=True)
    assert kept == []


def test_partially_valid_citations_are_trimmed_and_flagged():
    bundle = _bundle_with_refs([5, 6])
    mixed = Hypothesis(
        id="HYP_Z",
        failure_id="FAIL_X",
        statement="Partly grounded.",
        confidence=0.6,
        evidence_refs=[5, 404],
    )
    kept = validate_hypotheses([mixed], bundle, drop_unflagged=False)
    assert len(kept) == 1
    assert kept[0].evidence_refs == [5]
    assert kept[0].flagged is True


def test_valid_hypothesis_survives():
    bundle = _bundle_with_refs([7, 8, 9])
    good = Hypothesis(
        id="HYP_OK",
        failure_id="FAIL_X",
        statement="Grounded cause.",
        confidence=0.75,
        evidence_refs=[7, 8],
    )
    kept = validate_hypotheses([good], bundle)
    assert len(kept) == 1
    assert kept[0].flagged is False


def test_mock_llm_only_cites_real_evidence():
    # End-to-end: mock LLM must never cite a line outside the bundle.
    generated = generate_log(scenarios=["pcie_link"], noise_lines=4, seed=5)
    lines = parse_log(generated.text)
    failures = detect_failures(lines)
    bundles = build_evidence_bundles(failures, lines)
    from app.triage.runner import triage_failure

    for failure in failures:
        bundle = next(b for b in bundles if b.failure_id == failure.id)
        hyps, _ = triage_failure(failure, bundle)
        allowed = set(bundle.evidence_line_refs)
        for hyp in hyps:
            assert set(hyp.evidence_refs).issubset(allowed)
