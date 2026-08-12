"""
Pulse Guardian ICU — FastAPI Backend
=====================================
Academic/demo system for ICU clinical decision support.
Based on MIMIC-III clinical database.
NOT FOR REAL CLINICAL USE.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, SessionLocal
from app.models.user import (User, Patient, Admission, ICUStay,
                              RiskScore, Alert, Report, Base)
from app.api.auth import router as auth_router
from app.api.patients import router as patients_router
from app.api.routes import risk_router, alerts_router, reports_router, data_router, monitor_router

# ── Create all tables ──────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pulse Guardian ICU",
    description="AI-powered ICU Clinical Decision Support System (Academic Demo)",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# ── CORS ───────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(patients_router)
app.include_router(risk_router)
app.include_router(alerts_router)
app.include_router(reports_router)
app.include_router(data_router)
app.include_router(monitor_router)

# ── Startup: seed default user + demo data ─────────────────────────────────
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        from app.services.data_loader import seed_default_user, generate_synthetic_data
        seed_default_user(db)
        # Auto-generate demo data if DB is empty
        if db.query(Patient).count() == 0:
            print("No patients found — generating demo data...")
            generate_synthetic_data(db, n=200)
    finally:
        db.close()

@app.get("/")
def root():
    return {
        "name": "Pulse Guardian ICU API",
        "version": "1.0.0",
        "status": "running",
        "note": "Academic/demo use only — not for clinical decisions",
        "docs": "/api/docs"
    }

@app.get("/health")
def health():
    return {"status": "ok"}
