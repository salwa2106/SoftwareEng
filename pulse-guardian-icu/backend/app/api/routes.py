import asyncio
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json, os, shutil
from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user
from app.models.user import Patient, Admission, ICUStay, RiskScore, Alert, Report, User
from app.ml.risk_engine import calculate_risk_score, get_model_evaluation_metrics, predict_ml_mortality_risk
from app.services.live_monitor import MonitorSession

# ── Risk Router ────────────────────────────────────────────────────────────
risk_router = APIRouter(prefix="/api/risk", tags=["Risk"])

@risk_router.get("/metrics")
def model_metrics(current_user: User = Depends(get_current_user)):
    return get_model_evaluation_metrics()

@risk_router.get("/{hadm_id}")
def get_risk_by_admission(hadm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    risk = db.query(RiskScore).filter(RiskScore.hadm_id == hadm_id).order_by(RiskScore.calculated_at.desc()).first()
    if not risk:
        raise HTTPException(status_code=404, detail="Risk score not found")

    ml_prediction = None
    icu = db.query(ICUStay).filter(ICUStay.hadm_id == hadm_id).first()
    if icu:
        ml_prediction = predict_ml_mortality_risk({
            "heart_rate": icu.heart_rate_mean, "resp_rate": icu.resp_rate_mean,
            "spo2": icu.spo2_mean, "bp_systolic": icu.bp_systolic_mean,
            "bp_diastolic": icu.bp_diastolic_mean, "creatinine": icu.creatinine_mean,
            "glucose": icu.glucose_mean, "hemoglobin": icu.hemoglobin_mean,
            "potassium": icu.potassium_mean, "sodium": icu.sodium_mean,
            "wbc": icu.wbc_mean, "icu_los": icu.los,
        })

    return {
        "hadm_id": hadm_id,
        "score": risk.score,
        "risk_level": risk.risk_level,
        "contributing_factors": json.loads(risk.contributing_factors) if risk.contributing_factors else [],
        "calculated_at": str(risk.calculated_at),
        "ml_prediction": ml_prediction,
    }

@risk_router.post("/calculate")
def calculate_risk(data: dict, current_user: User = Depends(get_current_user)):
    """Ad-hoc risk calculation without saving."""
    result = calculate_risk_score(data)
    return result


# ── Live Monitor Router (simulated real-time vitals + alerts) ──────────────
monitor_router = APIRouter(prefix="/api/monitor", tags=["Monitor"])

TICK_SECONDS = 1.5
MAX_TICKS = 200  # ~5 minutes of simulated monitoring per session


@monitor_router.get("/{icustay_id}/stream")
async def stream_live_monitor(
    icustay_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Server-Sent Events stream that simulates a live ICU monitor for one
    patient. See app/services/live_monitor.py for why this is a
    disclosed simulation rather than a fabricated "real-time" claim:
    the source dataset only has per-stay aggregated vitals, not a raw
    waveform to replay.
    """
    db = SessionLocal()
    try:
        icu = db.query(ICUStay).filter(ICUStay.icustay_id == icustay_id).first()
        if not icu:
            raise HTTPException(status_code=404, detail="ICU stay not found")
        session = MonitorSession(icu, icu_los=icu.los)
    finally:
        db.close()

    async def event_generator():
        yield "event: open\ndata: {\"simulated\": true, \"note\": \"Simulated live monitor for demo purposes. Source dataset has per-stay aggregated vitals only \\u2014 not a real device feed.\"}\n\n"
        for tick in range(MAX_TICKS):
            if await request.is_disconnected():
                break
            payload = session.tick()
            payload["tick"] = tick
            yield f"data: {json.dumps(payload)}\n\n"
            await asyncio.sleep(TICK_SECONDS)
        yield "event: close\ndata: {\"reason\": \"session_ended\"}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ── Alerts Router ──────────────────────────────────────────────────────────
alerts_router = APIRouter(prefix="/api/alerts", tags=["Alerts"])

@alerts_router.get("/")
def get_all_alerts(
    severity: Optional[str] = None,
    acknowledged: Optional[bool] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity)
    if acknowledged is not None:
        query = query.filter(Alert.is_acknowledged == acknowledged)

    alerts = query.order_by(Alert.created_at.desc()).limit(limit).all()
    return [
        {"id": a.id, "hadm_id": a.hadm_id, "icustay_id": a.icustay_id,
         "type": a.alert_type, "severity": a.severity, "message": a.message,
         "indicator": a.indicator, "value": a.value, "acknowledged": a.is_acknowledged,
         "created_at": str(a.created_at)}
        for a in alerts
    ]

@alerts_router.patch("/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_acknowledged = True
    db.commit()
    return {"message": "Alert acknowledged"}


# ── Reports Router ─────────────────────────────────────────────────────────
reports_router = APIRouter(prefix="/api/reports", tags=["Reports"])

@reports_router.post("/{hadm_id}/generate")
def generate_report(hadm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    admission = db.query(Admission).filter(Admission.hadm_id == hadm_id).first()
    if not admission:
        raise HTTPException(status_code=404, detail="Admission not found")

    patient = db.query(Patient).filter(Patient.subject_id == admission.subject_id).first()
    icu = db.query(ICUStay).filter(ICUStay.hadm_id == hadm_id).first()
    risk = db.query(RiskScore).filter(RiskScore.hadm_id == hadm_id).first()
    alerts = db.query(Alert).filter(Alert.hadm_id == hadm_id).all()
    factors = json.loads(risk.contributing_factors) if risk and risk.contributing_factors else []

    critical_alerts = [a for a in alerts if a.severity == "critical"]
    warning_alerts  = [a for a in alerts if a.severity == "warning"]

    report_content = f"""
═══════════════════════════════════════════════════════
         PULSE GUARDIAN ICU — CLINICAL REPORT
         FOR ACADEMIC/DEMO USE ONLY
═══════════════════════════════════════════════════════

PATIENT INFORMATION
───────────────────
Patient ID:        {patient.subject_id if patient else 'N/A'}
Gender:            {patient.gender if patient else 'N/A'}
Age:               {patient.age if patient else 'N/A'} years
Admission ID:      {hadm_id}
Admission Type:    {admission.admission_type}
Admit Date:        {admission.admittime}
Discharge Date:    {admission.dischtime}
Hospital LOS:      {admission.hospital_los:.1f} days
Primary Diagnosis: {admission.diagnosis}

ICU STAY DETAILS
────────────────
{"ICU Stay ID:    " + str(icu.icustay_id) if icu else "No ICU stay recorded"}
{"Care Unit:      " + str(icu.first_careunit) if icu else ""}
{"ICU LOS:        " + str(round(icu.los, 1)) + " days" if icu else ""}

VITAL SIGNS (ICU Mean Values)
─────────────────────────────
{"Heart Rate:      " + str(icu.heart_rate_mean) + " bpm (normal: 60-100)" if icu else ""}
{"Resp. Rate:      " + str(icu.resp_rate_mean) + " /min (normal: 12-20)" if icu else ""}
{"SpO₂:            " + str(icu.spo2_mean) + " % (normal: ≥95)" if icu else ""}
{"BP Systolic:     " + str(icu.bp_systolic_mean) + " mmHg (normal: 90-140)" if icu else ""}
{"BP Diastolic:    " + str(icu.bp_diastolic_mean) + " mmHg (normal: 60-90)" if icu else ""}

LAB RESULTS (ICU Mean Values)
──────────────────────────────
{"Creatinine:      " + str(icu.creatinine_mean) + " mg/dL (normal: 0.6-1.2)" if icu else ""}
{"Glucose:         " + str(icu.glucose_mean) + " mg/dL (normal: 70-140)" if icu else ""}
{"Hemoglobin:      " + str(icu.hemoglobin_mean) + " g/dL (normal: 12-17)" if icu else ""}
{"Potassium:       " + str(icu.potassium_mean) + " mEq/L (normal: 3.5-5.0)" if icu else ""}
{"Sodium:          " + str(icu.sodium_mean) + " mEq/L (normal: 136-145)" if icu else ""}
{"WBC:             " + str(icu.wbc_mean) + " K/uL (normal: 4.5-11)" if icu else ""}

RISK ASSESSMENT
───────────────
Risk Score:  {risk.score if risk else 'N/A'} / 100
Risk Level:  {risk.risk_level if risk else 'N/A'}

Contributing Factors (top contributors):
{chr(10).join([f"  • {f['indicator'].replace('_',' ').title()}: {f['value']} — {f['status']} ({f['contribution']}% contribution)" for f in factors[:5]]) if factors else "  None identified"}

ALERTS SUMMARY
──────────────
Critical Alerts:  {len(critical_alerts)}
Warning Alerts:   {len(warning_alerts)}

{"Critical: " + chr(10).join(["  ⚠ " + a.message for a in critical_alerts]) if critical_alerts else "No critical alerts"}

CLINICAL NOTE
─────────────
This report was automatically generated by Pulse Guardian ICU.
All values reflect aggregated ICU stay measurements.
This system is intended for academic/demo purposes only.
Clinical decisions must be made by qualified healthcare professionals.

Generated by: {current_user.full_name or current_user.username}
═══════════════════════════════════════════════════════
"""

    report = Report(hadm_id=hadm_id, generated_by=current_user.id, content=report_content)
    db.add(report)
    db.commit()
    db.refresh(report)

    return {"report_id": report.id, "hadm_id": hadm_id, "content": report_content, "created_at": str(report.created_at)}

@reports_router.get("/{hadm_id}")
def get_reports(hadm_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    reports = db.query(Report).filter(Report.hadm_id == hadm_id).order_by(Report.created_at.desc()).all()
    return [{"id": r.id, "hadm_id": r.hadm_id, "content": r.content, "created_at": str(r.created_at)} for r in reports]


# ── Data Import Router ─────────────────────────────────────────────────────
data_router = APIRouter(prefix="/api/data", tags=["Data"])

@data_router.post("/import")
async def import_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    limit: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    os.makedirs("./data", exist_ok=True)
    dest = f"./data/{file.filename}"
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    from app.services.data_loader import load_dataset
    result = load_dataset(db, dest, limit=limit)
    return {"message": "Dataset imported successfully", "stats": result}

@data_router.post("/generate-demo")
def generate_demo(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    from app.services.data_loader import generate_synthetic_data
    result = generate_synthetic_data(db, n=200)
    return {"message": "Demo data generated", "stats": result}

@data_router.get("/status")
def data_status(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.user import Patient, Admission, ICUStay, RiskScore, Alert
    return {
        "patients": db.query(Patient).count(),
        "admissions": db.query(Admission).count(),
        "icustays": db.query(ICUStay).count(),
        "risk_scores": db.query(RiskScore).count(),
        "alerts": db.query(Alert).count(),
    }
