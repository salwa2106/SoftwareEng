"""
Simulated live ICU monitor.
============================
Addresses the reviewer note that the dashboard's data and alerts were
not real-time: MIMIC-III (and this project's dataset) only contains
per-stay AGGREGATED vitals (mean/min/max over the whole ICU stay), not
a raw per-second waveform, so there is no genuine live feed to replay.

Building a fake "live device feed" without saying so would be
dishonest. Instead, this module honestly SIMULATES a monitor: for a
given patient, it generates a physiologically plausible reading every
tick via a bounded random walk constrained to that patient's own
recorded [min, max] range for each vital, and re-runs the same
risk-scoring logic the rest of the app uses on every tick, so alerts
fire live as the simulated trajectory crosses thresholds — exercising
the same alerting code path a real live feed would use.

Every payload sent to the client is marked "simulated": true and the
UI must present it as a demo, never as a genuine device feed.
"""

import random
from typing import Dict, Optional

from app.ml.risk_engine import calculate_risk_score, detect_deterioration

# (indicator_key, mean_col, min_col, max_col)
_VITAL_FIELDS = [
    ("heart_rate", "heart_rate_mean", "heart_rate_min", "heart_rate_max"),
    ("resp_rate", "resp_rate_mean", "resp_rate_min", "resp_rate_max"),
    ("spo2", "spo2_mean", "spo2_min", "spo2_max"),
    ("bp_systolic", "bp_systolic_mean", "bp_systolic_min", "bp_systolic_max"),
    ("bp_diastolic", "bp_diastolic_mean", "bp_diastolic_min", "bp_diastolic_max"),
]
# Labs change slowly in reality; nudge gently around the recorded mean
# rather than walking them every tick like vitals.
_LAB_FIELDS = [
    ("creatinine", "creatinine_mean"),
    ("glucose", "glucose_mean"),
    ("hemoglobin", "hemoglobin_mean"),
    ("potassium", "potassium_mean"),
    ("sodium", "sodium_mean"),
    ("wbc", "wbc_mean"),
]


class MonitorSession:
    """Holds the evolving simulated-vitals state for one live-monitor connection."""

    def __init__(self, icu, icu_los: Optional[float]):
        self.icu = icu
        self.icu_los = icu_los
        self.current: Dict[str, float] = {}
        self.previous_result: Optional[Dict] = None

        for key, mean_col, min_col, max_col in _VITAL_FIELDS:
            mean = getattr(icu, mean_col, None)
            self.current[key] = mean if mean is not None else 0.0

        for key, mean_col in _LAB_FIELDS:
            self.current[key] = getattr(icu, mean_col, None)

    def _bounded_walk(self, key: str, mean_col: str, min_col: str, max_col: str) -> float:
        mean = getattr(self.icu, mean_col, None)
        lo = getattr(self.icu, min_col, None)
        hi = getattr(self.icu, max_col, None)
        current = self.current.get(key, mean or 0.0)

        if mean is None:
            return current

        # Bound the walk to the patient's own recorded range, widened
        # slightly so the simulation can still explore near the edges.
        lo = lo if lo is not None else mean * 0.85
        hi = hi if hi is not None else mean * 1.15
        span = max(hi - lo, 1e-6)

        step = random.gauss(0, span * 0.06)
        # Gentle pull back toward the mean so the walk doesn't drift away.
        pull = (mean - current) * 0.05
        new_value = current + step + pull
        new_value = max(lo - span * 0.05, min(hi + span * 0.05, new_value))
        return round(new_value, 1)

    def tick(self) -> Dict:
        for key, mean_col, min_col, max_col in _VITAL_FIELDS:
            self.current[key] = self._bounded_walk(key, mean_col, min_col, max_col)

        risk_input = dict(self.current)
        risk_input["icu_los"] = self.icu_los
        result = calculate_risk_score(risk_input)

        new_events = []
        if self.previous_result is not None:
            new_events = detect_deterioration(result, self.previous_result)
        self.previous_result = result

        return {
            "simulated": True,
            "icustay_id": self.icu.icustay_id,
            "vitals": {k: self.current[k] for k, *_ in _VITAL_FIELDS},
            "score": result["score"],
            "risk_level": result["risk_level"],
            "alerts": result["alerts"],
            "new_events": new_events,
        }
