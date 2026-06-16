from fastapi import APIRouter
from app.services.data_loader import data_loader

router = APIRouter()

@router.get("/health")
def health_check():
    patient_ids = data_loader.get_patient_ids()
    return {
        "status": "ok",
        "data_loaded": len(patient_ids) > 0,
        "patient_count": len(patient_ids),
        "message": "ICU Risk Prediction API is running. NOT for clinical use."
    }
