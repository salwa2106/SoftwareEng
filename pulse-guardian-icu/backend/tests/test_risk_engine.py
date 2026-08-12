"""
Unit tests for the rule-based risk engine.

Before this project had any tests at all, correctness of the risk
scoring logic — the core of the whole system — was verified only by
eyeballing the dashboard. These tests pin down the documented
contract (normal ranges, risk bands, deterioration detection) so a
future change that breaks it fails in CI, not in front of the class.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ml.risk_engine import (
    calculate_risk_score,
    detect_deterioration,
    get_model_evaluation_metrics,
)

NORMAL_PATIENT = {
    "heart_rate": 75, "resp_rate": 16, "spo2": 98,
    "bp_systolic": 115, "bp_diastolic": 75,
    "creatinine": 0.9, "glucose": 95, "hemoglobin": 14,
    "potassium": 4.0, "sodium": 140, "wbc": 7, "icu_los": 1,
}

CRITICAL_PATIENT = {
    "heart_rate": 160, "resp_rate": 35, "spo2": 80,
    "bp_systolic": 60, "bp_diastolic": 30,
    "creatinine": 5.0, "glucose": 450, "hemoglobin": 6,
    "potassium": 7.0, "sodium": 160, "wbc": 35, "icu_los": 20,
}


def test_all_normal_vitals_score_low():
    result = calculate_risk_score(NORMAL_PATIENT)
    assert result["risk_level"] == "Low"
    assert result["score"] < 40
    assert result["contributing_factors"] == []
    assert result["alerts"] == []


def test_all_critical_vitals_score_high():
    result = calculate_risk_score(CRITICAL_PATIENT)
    assert result["risk_level"] == "High"
    assert result["score"] >= 70
    assert result["critical_count"] > 0
    assert any(a["type"] == "critical" for a in result["alerts"])


def test_score_is_bounded_0_to_100():
    result = calculate_risk_score(CRITICAL_PATIENT)
    assert 0 <= result["score"] <= 100


def test_missing_values_are_treated_as_unknown_not_penalized():
    sparse = {"heart_rate": 75, "icu_los": 0}
    result = calculate_risk_score(sparse)
    assert result["indicator_details"]["spo2"]["status"] == "unknown"
    assert result["indicator_details"]["spo2"]["contribution_score"] == 0


def test_icu_los_adds_penalty_independent_of_vitals():
    short_stay = calculate_risk_score({**NORMAL_PATIENT, "icu_los": 1})
    long_stay = calculate_risk_score({**NORMAL_PATIENT, "icu_los": 20})
    assert long_stay["score"] > short_stay["score"]


def test_contributing_factors_sorted_by_contribution_descending():
    result = calculate_risk_score(CRITICAL_PATIENT)
    contributions = [f["contribution"] for f in result["contributing_factors"]]
    assert contributions == sorted(contributions, reverse=True)


def test_detect_deterioration_flags_rising_score():
    previous = calculate_risk_score(NORMAL_PATIENT)
    current = calculate_risk_score(CRITICAL_PATIENT)
    events = detect_deterioration(current, previous)
    assert any(e["type"] == "deterioration" for e in events)


def test_detect_deterioration_silent_when_stable():
    previous = calculate_risk_score(NORMAL_PATIENT)
    current = calculate_risk_score(NORMAL_PATIENT)
    events = detect_deterioration(current, previous)
    assert events == []


def test_model_evaluation_metrics_are_not_hardcoded_placeholders():
    """
    Regression test for the exact bug flagged in review: metrics.json
    must exist and be internally consistent, not the literal
    {0.847, 0.831, ...} values that used to be hand-typed into the
    source file.
    """
    metrics = get_model_evaluation_metrics()
    assert "error" not in metrics, (
        "Run `python -m app.ml.train_model` to generate "
        "app/ml/artifacts/metrics.json before running tests."
    )
    assert 0.5 <= metrics["ml_model"]["test_auc_roc"] <= 1.0
    assert metrics["dataset"]["n_rows"] > 1000
    assert metrics["ml_model"]["test_auc_roc"] >= metrics["baseline_rule_engine"]["auc_roc"], (
        "Trained model should not perform worse than the untrained "
        "hand-tuned baseline on held-out data."
    )
