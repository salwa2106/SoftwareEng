from typing import List, Dict, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

RISK_VALUES = {"Low": 25.0, "Medium": 55.0, "High": 85.0}

class RiskEngine:
    """
    Rule-based risk scoring engine.
    NOTE: This is NOT clinically validated. For demonstration only.
    """

    def score_hourly(self, features: dict) -> dict:
        triggers = []
        critical_triggers = []

        hr = features.get("heart_rate")
        rr = features.get("resp_rate")
        spo2 = features.get("spo2")
        temp = features.get("temperature")
        wbc = features.get("wbc")
        creatinine = features.get("creatinine")
        lactate = features.get("lactate")
        hemoglobin = features.get("hemoglobin")
        platelets = features.get("platelets")

        if hr is not None:
            if hr > 130:
                critical_triggers.append(f"Heart rate critically high ({hr:.0f} bpm)")
            elif hr > settings.HEART_RATE_HIGH:
                triggers.append(f"Heart rate elevated ({hr:.0f} bpm)")
            elif hr < 50:
                critical_triggers.append(f"Heart rate critically low ({hr:.0f} bpm)")
            elif hr < settings.HEART_RATE_LOW:
                triggers.append(f"Heart rate low ({hr:.0f} bpm)")

        if rr is not None:
            if rr > 30:
                critical_triggers.append(f"Respiratory rate critically high ({rr:.0f} breaths/min)")
            elif rr > settings.RESP_RATE_HIGH:
                triggers.append(f"Respiratory rate elevated ({rr:.0f} breaths/min)")
            elif rr < settings.RESP_RATE_LOW:
                triggers.append(f"Respiratory rate low ({rr:.0f} breaths/min)")

        if spo2 is not None:
            if spo2 < 90:
                critical_triggers.append(f"SpO2 critically low ({spo2:.1f}%)")
            elif spo2 < settings.SPO2_LOW:
                triggers.append(f"SpO2 below normal ({spo2:.1f}%)")

        if temp is not None:
            if temp > 39.5:
                critical_triggers.append(f"High fever ({temp:.1f}°C)")
            elif temp > settings.TEMP_HIGH:
                triggers.append(f"Fever ({temp:.1f}°C)")
            elif temp < 35:
                critical_triggers.append(f"Hypothermia ({temp:.1f}°C)")
            elif temp < settings.TEMP_LOW:
                triggers.append(f"Low temperature ({temp:.1f}°C)")

        if wbc is not None:
            if wbc > 20:
                critical_triggers.append(f"WBC critically elevated ({wbc:.1f} K/uL)")
            elif wbc > settings.WBC_HIGH:
                triggers.append(f"WBC above normal ({wbc:.1f} K/uL)")
            elif wbc < 2:
                critical_triggers.append(f"WBC critically low ({wbc:.1f} K/uL)")
            elif wbc < settings.WBC_LOW:
                triggers.append(f"WBC below normal ({wbc:.1f} K/uL)")

        if creatinine is not None:
            if creatinine > 3.0:
                critical_triggers.append(f"Creatinine critically elevated ({creatinine:.2f} mg/dL)")
            elif creatinine > settings.CREATININE_HIGH:
                triggers.append(f"Creatinine elevated ({creatinine:.2f} mg/dL)")

        if lactate is not None:
            if lactate > 4.0:
                critical_triggers.append(f"Lactate critically high ({lactate:.2f} mmol/L) - possible septic shock")
            elif lactate > 2.0:
                critical_triggers.append(f"Lactate elevated ({lactate:.2f} mmol/L)")
            elif lactate > settings.LACTATE_HIGH:
                triggers.append(f"Lactate above normal ({lactate:.2f} mmol/L)")

        if hemoglobin is not None and hemoglobin < settings.HEMOGLOBIN_LOW:
            triggers.append(f"Hemoglobin low ({hemoglobin:.1f} g/dL)")

        if platelets is not None and platelets < settings.PLATELETS_LOW:
            triggers.append(f"Platelets low ({platelets:.0f} K/uL)")

        total_abnormal = features.get("abnormal_count", 0)

        if len(critical_triggers) >= 2 or total_abnormal >= 5:
            risk_level = "High"
        elif len(critical_triggers) >= 1 or total_abnormal >= 3:
            risk_level = "High"
        elif total_abnormal >= 2 or len(triggers) >= 2:
            risk_level = "Medium"
        elif total_abnormal >= 1 or len(triggers) >= 1:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        all_triggers = critical_triggers + triggers

        return {
            "risk_level": risk_level,
            "risk_value": RISK_VALUES[risk_level],
            "triggers": all_triggers,
            "critical_count": len(critical_triggers),
            "warning_count": len(triggers)
        }

    def score_timeline(self, hourly_data: List[dict]) -> List[dict]:
        scored = []
        prev_risk = "Low"

        for hour_data in hourly_data:
            result = self.score_hourly(hour_data)
            hour_data["risk_score"] = result["risk_level"]
            hour_data["risk_value"] = result["risk_value"]
            hour_data["triggers"] = result["triggers"]
            hour_data["risk_changed"] = result["risk_level"] != prev_risk
            hour_data["prev_risk"] = prev_risk
            prev_risk = result["risk_level"]
            scored.append(hour_data)

        return scored

    def get_current_risk(self, hourly_data: List[dict]) -> dict:
        if not hourly_data:
            return {"risk_level": "Unknown", "risk_value": 0, "triggers": [], "trend": "unknown"}

        scored = self.score_timeline(hourly_data)
        last = scored[-1]

        trend = "stable"
        if len(scored) >= 6:
            recent_risks = [h["risk_value"] for h in scored[-6:]]
            if recent_risks[-1] > recent_risks[0] + 10:
                trend = "worsening"
            elif recent_risks[-1] < recent_risks[0] - 10:
                trend = "improving"

        return {
            "risk_level": last.get("risk_score", "Low"),
            "risk_value": last.get("risk_value", 25),
            "triggers": last.get("triggers", []),
            "trend": trend
        }

risk_engine = RiskEngine()
