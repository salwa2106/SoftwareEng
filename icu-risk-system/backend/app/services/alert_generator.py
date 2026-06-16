from typing import List, Dict
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class AlertGenerator:
    """
    Generates clinical alerts when patient risk level increases.
    An alert is fired when risk transitions upward (Low->Medium, Medium->High, Low->High).
    """

    def generate_alerts(self, subject_id: int, scored_timeline: List[dict]) -> List[dict]:
        alerts = []

        for i, hour_data in enumerate(scored_timeline):
            if not hour_data.get("risk_changed", False):
                continue

            prev_risk = hour_data.get("prev_risk", "Low")
            curr_risk = hour_data.get("risk_score", "Low")

            risk_order = {"Low": 0, "Medium": 1, "High": 2}
            if risk_order.get(curr_risk, 0) <= risk_order.get(prev_risk, 0):
                continue

            severity = "critical" if curr_risk == "High" else "warning"
            triggers = hour_data.get("triggers", [])

            alert = {
                "alert_id": str(uuid.uuid4())[:8],
                "subject_id": subject_id,
                "hour": hour_data["hour"],
                "timestamp": hour_data["timestamp"],
                "severity": severity,
                "triggers": triggers if triggers else [f"Risk elevated to {curr_risk}"],
                "risk_before": prev_risk,
                "risk_after": curr_risk,
                "details": {
                    "heart_rate": hour_data.get("heart_rate"),
                    "resp_rate": hour_data.get("resp_rate"),
                    "spo2": hour_data.get("spo2"),
                    "wbc": hour_data.get("wbc"),
                    "creatinine": hour_data.get("creatinine"),
                    "lactate": hour_data.get("lactate"),
                }
            }
            alerts.append(alert)

        return alerts

alert_generator = AlertGenerator()
