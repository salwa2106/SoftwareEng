from fastapi import APIRouter, HTTPException
from app.services.timeline_builder import timeline_builder
from app.services.risk_engine import risk_engine

router = APIRouter()

@router.get("/patients/{patient_id}/risk")
def get_risk(patient_id: int):
    """Return current risk score for patient."""
    result = timeline_builder.build_timeline(patient_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No data for patient {patient_id}")

    scored = risk_engine.score_timeline(result["hourly_data"])
    current = risk_engine.get_current_risk(scored)

    latest = scored[-1] if scored else {}
    abnormal_values = {}
    for key in ["heart_rate", "resp_rate", "spo2", "temperature", "wbc", "creatinine", "lactate", "hemoglobin"]:
        val = latest.get(key)
        if val is not None:
            abnormal_values[key] = val

    return {
        "subject_id": patient_id,
        "timestamp": latest.get("timestamp", ""),
        "risk_level": current["risk_level"],
        "risk_value": current["risk_value"],
        "abnormal_values": abnormal_values,
        "trend": current["trend"],
        "triggers": current["triggers"]
    }
