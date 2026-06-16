from fastapi import APIRouter, HTTPException
from app.services.timeline_builder import timeline_builder
from app.services.risk_engine import risk_engine

router = APIRouter()

@router.get("/patients/{patient_id}/timeline")
def get_timeline(patient_id: int, max_hours: int = 72):
    """Return hourly timeline with risk scores for patient."""
    result = timeline_builder.build_timeline(patient_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No timeline data for patient {patient_id}")

    result["hourly_data"] = risk_engine.score_timeline(result["hourly_data"])
    result["hourly_data"] = result["hourly_data"][:max_hours]

    return result
