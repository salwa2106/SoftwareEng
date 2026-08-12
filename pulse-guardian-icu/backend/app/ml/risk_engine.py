"""
Pulse Guardian ICU - Risk Prediction Engine
============================================
Rule-based risk scoring engine with ML-ready architecture.
FOR ACADEMIC/DEMO USE ONLY - Not for real clinical decisions.

Risk Score: 0-100
  0-39  = Low Risk (Green)
  40-69 = Medium Risk (Yellow)
  70-100 = High Risk (Red)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
import json
import os

# ── Clinical reference ranges (normal limits) ──────────────────────────────
NORMAL_RANGES = {
    "heart_rate":      {"low": 60,  "high": 100, "critical_low": 40,  "critical_high": 150},
    "resp_rate":       {"low": 12,  "high": 20,  "critical_low": 8,   "critical_high": 30},
    "spo2":            {"low": 95,  "high": 100, "critical_low": 88,  "critical_high": None},
    "bp_systolic":     {"low": 90,  "high": 140, "critical_low": 70,  "critical_high": 180},
    "bp_diastolic":    {"low": 60,  "high": 90,  "critical_low": 40,  "critical_high": 120},
    "creatinine":      {"low": 0.6, "high": 1.2, "critical_low": None,"critical_high": 4.0},
    "glucose":         {"low": 70,  "high": 140, "critical_low": 50,  "critical_high": 400},
    "hemoglobin":      {"low": 12,  "high": 17,  "critical_low": 7,   "critical_high": None},
    "potassium":       {"low": 3.5, "high": 5.0, "critical_low": 2.5, "critical_high": 6.5},
    "sodium":          {"low": 136, "high": 145, "critical_low": 125, "critical_high": 155},
    "wbc":             {"low": 4.5, "high": 11,  "critical_low": None,"critical_high": 30},
}

# ── Weights for each indicator ──────────────────────────────────────────────
INDICATOR_WEIGHTS = {
    "heart_rate":   12,
    "resp_rate":    12,
    "spo2":         15,   # highest weight — most critical
    "bp_systolic":  10,
    "bp_diastolic": 8,
    "creatinine":   10,
    "glucose":      7,
    "hemoglobin":   8,
    "potassium":    8,
    "sodium":       5,
    "wbc":          5,
}

# ── ICU LOS penalty ────────────────────────────────────────────────────────
ICU_LOS_THRESHOLDS = [
    (3,  0),   # < 3 days: no penalty
    (7,  5),   # 3–7 days: +5
    (14, 10),  # 7–14 days: +10
    (float("inf"), 15),  # >14 days: +15
]


def _score_indicator(name: str, value: Optional[float]) -> Tuple[float, str, bool]:
    """
    Returns (penalty_0_to_1, status_label, is_critical)
    penalty_0_to_1: 0 = normal, 1 = maximally abnormal
    """
    if value is None or np.isnan(value):
        return 0.0, "unknown", False

    r = NORMAL_RANGES[name]
    low, high = r["low"], r["high"]
    crit_low, crit_high = r.get("critical_low"), r.get("critical_high")

    if low <= value <= high:
        return 0.0, "normal", False

    # Below normal range
    if value < low:
        is_critical = crit_low is not None and value <= crit_low
        if is_critical:
            penalty = 1.0
            status = "critical_low"
        else:
            # Linear interpolation between low and critical_low
            if crit_low is not None:
                penalty = min(1.0, (low - value) / (low - crit_low))
            else:
                penalty = min(1.0, (low - value) / max(low * 0.3, 1))
            status = "abnormal_low"
        return penalty, status, is_critical

    # Above normal range
    if value > high:
        is_critical = crit_high is not None and value >= crit_high
        if is_critical:
            penalty = 1.0
            status = "critical_high"
        else:
            if crit_high is not None:
                penalty = min(1.0, (value - high) / (crit_high - high))
            else:
                penalty = min(1.0, (value - high) / max(high * 0.3, 1))
            status = "abnormal_high"
        return penalty, status, is_critical

    return 0.0, "normal", False


def calculate_risk_score(patient_data: Dict) -> Dict:
    """
    Main risk scoring function.
    
    Input: dict with keys matching INDICATOR_WEIGHTS + optional 'icu_los'
    Output: {
        score: float (0–100),
        risk_level: str,
        contributing_factors: list,
        alerts: list,
        indicator_details: dict
    }
    """
    total_weight = sum(INDICATOR_WEIGHTS.values())
    weighted_penalty = 0.0
    contributing_factors = []
    alerts = []
    indicator_details = {}
    critical_count = 0

    for indicator, weight in INDICATOR_WEIGHTS.items():
        value = patient_data.get(indicator)
        if value is not None:
            try:
                value = float(value)
            except (ValueError, TypeError):
                value = None

        penalty, status, is_critical = _score_indicator(indicator, value)
        contribution = penalty * weight

        indicator_details[indicator] = {
            "value": value,
            "status": status,
            "is_critical": is_critical,
            "normal_range": NORMAL_RANGES[indicator],
            "contribution_score": round(contribution, 2),
        }

        if penalty > 0:
            weighted_penalty += contribution
            contributing_factors.append({
                "indicator": indicator,
                "value": value,
                "status": status,
                "contribution": round(contribution / total_weight * 100, 1),
                "is_critical": is_critical,
            })

            if is_critical:
                critical_count += 1
                alerts.append({
                    "type": "critical",
                    "indicator": indicator,
                    "value": value,
                    "message": f"CRITICAL: {indicator.replace('_', ' ').title()} = {value} — requires immediate attention",
                    "severity": "critical",
                })
            elif penalty > 0.5:
                alerts.append({
                    "type": "warning",
                    "indicator": indicator,
                    "value": value,
                    "message": f"WARNING: {indicator.replace('_', ' ').title()} = {value} — outside normal range",
                    "severity": "warning",
                })

    # Base score from indicators
    base_score = (weighted_penalty / total_weight) * 85  # max 85 from indicators

    # ICU LOS bonus
    icu_los = patient_data.get("icu_los", 0) or 0
    los_penalty = 0
    for threshold, penalty in ICU_LOS_THRESHOLDS:
        if icu_los < threshold:
            los_penalty = penalty
            break

    # Critical count bonus (multiple critical = higher risk)
    critical_bonus = min(15, critical_count * 5)

    final_score = min(100, base_score + los_penalty + critical_bonus)

    # Determine risk level
    if final_score < 40:
        risk_level = "Low"
    elif final_score < 70:
        risk_level = "Medium"
    else:
        risk_level = "High"

    # Sort contributing factors by contribution descending
    contributing_factors.sort(key=lambda x: x["contribution"], reverse=True)

    return {
        "score": round(final_score, 1),
        "risk_level": risk_level,
        "contributing_factors": contributing_factors,
        "alerts": alerts,
        "indicator_details": indicator_details,
        "critical_count": critical_count,
    }


def detect_deterioration(current: Dict, previous: Dict) -> List[Dict]:
    """
    Compare two risk snapshots and return deterioration events.
    """
    events = []

    current_score = current.get("score", 0)
    prev_score = previous.get("score", 0)

    if current_score - prev_score >= 10:
        events.append({
            "type": "deterioration",
            "message": f"Risk score increased by {current_score - prev_score:.1f} points",
            "severity": "critical" if current_score >= 70 else "warning",
        })

    # Check individual indicators
    vital_indicators = ["spo2", "heart_rate", "resp_rate", "bp_systolic"]
    for ind in vital_indicators:
        curr_val = current.get("indicator_details", {}).get(ind, {}).get("value")
        prev_status = previous.get("indicator_details", {}).get(ind, {}).get("status")
        curr_status = current.get("indicator_details", {}).get(ind, {}).get("status")

        if curr_status in ("critical_low", "critical_high") and prev_status == "normal":
            events.append({
                "type": "new_critical",
                "indicator": ind,
                "message": f"{ind.replace('_', ' ').title()} became critical (value: {curr_val})",
                "severity": "critical",
            })

    return events


_METRICS_CACHE = None
_ARTIFACT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "artifacts", "metrics.json")


def get_model_evaluation_metrics() -> Dict:
    """
    Returns the REAL evaluation report produced by app/ml/train_model.py:
    a Random Forest trained on final_icu_dataset.csv, validated on a
    held-out test set + 5-fold CV, evaluated against the ground-truth
    HOSPITAL_EXPIRE_FLAG label, and compared against the rule-based
    engine in this file as the baseline.

    If the artifact hasn't been generated yet, run:
        cd backend && python -m app.ml.train_model
    """
    global _METRICS_CACHE
    if _METRICS_CACHE is None:
        if not os.path.exists(_ARTIFACT_PATH):
            return {
                "error": (
                    "No trained-model evaluation found. Run "
                    "`python -m app.ml.train_model` from the backend/ "
                    "directory to generate app/ml/artifacts/metrics.json."
                )
            }
        with open(_ARTIFACT_PATH) as f:
            _METRICS_CACHE = json.load(f)
    return _METRICS_CACHE


# ── Trained ML model inference (companion to the rule-based engine) ────────
_ML_MODEL = None
_ML_IMPUTER = None
_ML_FEATURE_ORDER = [
    "heart_rate", "resp_rate", "spo2", "bp_systolic", "bp_diastolic",
    "creatinine", "glucose", "hemoglobin", "potassium", "sodium", "wbc",
    "icu_los",
]


def _load_ml_artifacts():
    global _ML_MODEL, _ML_IMPUTER
    if _ML_MODEL is None:
        import joblib
        artifact_dir = os.path.dirname(_ARTIFACT_PATH)
        model_path = os.path.join(artifact_dir, "model.joblib")
        imputer_path = os.path.join(artifact_dir, "imputer.joblib")
        if not (os.path.exists(model_path) and os.path.exists(imputer_path)):
            return None, None
        _ML_MODEL = joblib.load(model_path)
        _ML_IMPUTER = joblib.load(imputer_path)
    return _ML_MODEL, _ML_IMPUTER


def predict_ml_mortality_risk(patient_data: Dict) -> Optional[Dict]:
    """
    Runs the trained Random Forest (see train_model.py) on a single
    patient's aggregated vitals/labs and returns a calibrated mortality
    probability, as a second, data-driven opinion alongside the
    rule-based score. Returns None if the model artifacts haven't been
    trained yet (run `python -m app.ml.train_model`).
    """
    model, imputer = _load_ml_artifacts()
    if model is None:
        return None

    row = [[patient_data.get(f) for f in _ML_FEATURE_ORDER]]
    row_imputed = imputer.transform(row)
    probability = float(model.predict_proba(row_imputed)[0][1])

    return {
        "mortality_probability": round(probability, 4),
        "model": "RandomForestClassifier (trained on final_icu_dataset.csv)",
    }
