from __future__ import annotations

from app.models.schemas import Severity
from app.triage.scoring import blend_confidence


def test_critical_scores_higher_than_warning_for_same_llm_confidence():
    crit = blend_confidence(0.5, Severity.CRITICAL)
    warn = blend_confidence(0.5, Severity.WARNING)
    assert crit > warn


def test_blend_is_weighted_average():
    # llm_weight 0.6: 0.6*1.0 + 0.4*1.0 (CRITICAL weight) = 1.0
    assert blend_confidence(1.0, Severity.CRITICAL) == 1.0
    # 0.6*0.0 + 0.4*0.25 (INFO weight) = 0.1
    assert blend_confidence(0.0, Severity.INFO) == 0.1


def test_result_clamped_to_unit_interval():
    assert 0.0 <= blend_confidence(5.0, Severity.CRITICAL) <= 1.0
    assert 0.0 <= blend_confidence(-5.0, Severity.INFO) <= 1.0


def test_llm_weight_one_ignores_severity():
    assert blend_confidence(0.42, Severity.CRITICAL, llm_weight=1.0) == 0.42
    assert blend_confidence(0.42, Severity.INFO, llm_weight=1.0) == 0.42


def test_llm_weight_zero_uses_only_severity():
    assert blend_confidence(0.99, Severity.WARNING, llm_weight=0.0) == 0.5
