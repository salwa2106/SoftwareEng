from fastapi import APIRouter, HTTPException
from app.services.timeline_builder import timeline_builder
from app.services.risk_engine import risk_engine
from app.services.alert_generator import alert_generator

router = APIRouter()

@router.get("/patients/{patient_id}/alerts")
def get_alerts(patient_id: int):
    """Return all clinical alerts for patient."""
    result = timeline_builder.build_timeline(patient_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No data for patient {patient_id}")

    scored = risk_engine.score_timeline(result["hourly_data"])
    alerts = alert_generator.generate_alerts(patient_id, scored)

    return {
        "subject_id": patient_id,
        "total_alerts": len(alerts),
        "alerts": alerts
    }
