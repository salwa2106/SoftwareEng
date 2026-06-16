from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api import health, patients, timeline, risk, alerts

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ICU Risk Prediction API",
    description="Dynamic risk prediction from temporal MIMIC-III patient data. NOT for clinical use.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["Health"])
app.include_router(patients.router, prefix="/api", tags=["Patients"])
app.include_router(timeline.router, prefix="/api", tags=["Timeline"])
app.include_router(risk.router, prefix="/api", tags=["Risk"])
app.include_router(alerts.router, prefix="/api", tags=["Alerts"])

@app.get("/")
def root():
    return {
        "message": "ICU Risk Prediction API",
        "docs": "/docs",
        "disclaimer": "This system is for academic demonstration only. NOT for clinical use."
    }
