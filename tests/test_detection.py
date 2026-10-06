from __future__ import annotations

from app.detection.matcher import detect_failures
from app.parsing.parser import parse_log
from app.synthetic.generator import SCENARIOS, generate_log

# Maps a synthetic scenario to the signature id its failure lines should trigger.
SCENARIO_TO_SIGNATURE = {
    "boot_hang": "SIG_BOOT_WATCHDOG",
    "thermal_trip": "SIG_THERMAL_TRIP",
    "memory_ecc": "SIG_MEM_UE",
    "pcie_link": "SIG_PCIE_LINK_FAIL",
    "power_rail": "SIG_PWR_VR_FAULT",
    "pattern_mismatch": "SIG_ATE_PATTERN_MISMATCH",
}


def test_each_scenario_detected_against_ground_truth():
    for scenario in SCENARIOS:
        generated = generate_log(scenarios=[scenario], noise_lines=6, seed=1)
        lines = parse_log(generated.text)
        failures = detect_failures(lines)
        found = {f.signature_id for f in failures}
        assert SCENARIO_TO_SIGNATURE[scenario] in found, scenario


def test_clean_log_produces_no_critical_failures():
    # noise-only log (no injected scenario lines)
    generated = generate_log(scenarios=[], noise_lines=12, seed=3)
    lines = parse_log(generated.text)
    failures = detect_failures(lines)
    assert all(f.severity.value != "CRITICAL" for f in failures)


def test_failures_carry_line_refs():
    generated = generate_log(scenarios=["thermal_trip"], noise_lines=4, seed=2)
    lines = parse_log(generated.text)
    failures = detect_failures(lines)
    assert failures
    assert all(f.line_refs for f in failures)
