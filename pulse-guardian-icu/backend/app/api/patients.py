from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
import json
from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import Patient, Admission, ICUStay, RiskScore, Alert, User

router = APIRouter(prefix="/api/patients", tags=["Patients"])

def _build_patient_summary(patient, admission, icu, risk):
    return {
        "subject_id":     patient.subject_id,
        "hadm_id":        admission.hadm_id      if admission else None,
        "icustay_id":     icu.icustay_id          if icu       else None,
        "gender":         patient.gender,
        "age":            patient.age,
        "admission_type": admission.admission_type if admission else None,
        "diagnosis":      admission.diagnosis      if admission else None,
        "hospital_los":   admission.hospital_los   if admission else None,
        "icu_los":        icu.los                  if icu       else None,
        "first_careunit": icu.first_careunit        if icu       else None,
        "risk_score":     risk.score               if risk      else None,
        "risk_level":     risk.risk_level           if risk      else None,
        "admittime":      admission.admittime       if admission else None,
    }

@router.get("/")
def get_patients(
    page:           int            = Query(1, ge=1),
    per_page:       int            = Query(20, ge=1, le=100),
    # Search
    search:         Optional[str]  = None,
    search_by:      Optional[str]  = None,   # subject_id | hadm_id | icustay_id
    # Filters
    risk_level:     Optional[str]  = None,
    gender:         Optional[str]  = None,
    admission_type: Optional[str]  = None,
    care_unit:      Optional[str]  = None,
    db:             Session        = Depends(get_db),
    current_user:   User           = Depends(get_current_user)
):
    query = (
        db.query(Patient, Admission, ICUStay, RiskScore)
        .join(Admission, Patient.subject_id == Admission.subject_id, isouter=True)
        .join(ICUStay,   Admission.hadm_id  == ICUStay.hadm_id,     isouter=True)
        .join(RiskScore, Admission.hadm_id  == RiskScore.hadm_id,   isouter=True)
    )

    # ── Search by specific ID type ────────────────────────────────────────
    if search and search.strip():
        search = search.strip()
        try:
            search_int = int(search)
            if search_by == "hadm_id":
                query = query.filter(Admission.hadm_id == search_int)
            elif search_by == "icustay_id":
                query = query.filter(ICUStay.icustay_id == search_int)
            else:
                # Default: search by subject_id
                query = query.filter(Patient.subject_id == search_int)
        except ValueError:
            # Non-numeric input — return empty results gracefully
            return {"total": 0, "page": page, "per_page": per_page, "pages": 0, "patients": []}

    # ── Filters ───────────────────────────────────────────────────────────
    if risk_level:
        query = query.filter(RiskScore.risk_level == risk_level)
    if gender:
        query = query.filter(Patient.gender == gender)
    if admission_type:
        query = query.filter(Admission.admission_type == admission_type)
    if care_unit:
        query = query.filter(ICUStay.first_careunit == care_unit)

    total   = query.count()
    results = query.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "total":    total,
        "page":     page,
        "per_page": per_page,
        "pages":    (total + per_page - 1) // per_page,
        "patients": [_build_patient_summary(p, a, i, r) for p, a, i, r in results]
    }


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from sqlalchemy import func

    total_patients   = db.query(Patient).count()
    total_admissions = db.query(Admission).count()
    high_risk        = db.query(RiskScore).filter(RiskScore.risk_level == "High").count()
    medium_risk      = db.query(RiskScore).filter(RiskScore.risk_level == "Medium").count()
    low_risk         = db.query(RiskScore).filter(RiskScore.risk_level == "Low").count()
    active_alerts    = db.query(Alert).filter(Alert.is_acknowledged == False).count()
    critical_alerts  = db.query(Alert).filter(Alert.severity == "critical", Alert.is_acknowledged == False).count()

    # Distinct care units for filter dropdown
    care_units = [
        r[0] for r in db.query(ICUStay.first_careunit).distinct().all()
        if r[0]
    ]
    # Distinct admission types for filter dropdown
    admission_types = [
        r[0] for r in db.query(Admission.admission_type).distinct().all()
        if r[0]
    ]

    return {
        "total_patients":   total_patients,
        "total_admissions": total_admissions,
        "risk_distribution": {"High": high_risk, "Medium": medium_risk, "Low": low_risk},
        "active_alerts":    active_alerts,
        "critical_alerts":  critical_alerts,
        "care_units":       sorted(care_units),
        "admission_types":  sorted(admission_types),
    }


@router.get("/{subject_id}")
def get_patient_detail(
    subject_id:   int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.subject_id == subject_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    admissions = db.query(Admission).filter(Admission.subject_id == subject_id).all()
    result = {
        "subject_id": patient.subject_id,
        "gender":     patient.gender,
        "age":        patient.age,
        "admissions": []
    }

    for adm in admissions:
        icu_stays = db.query(ICUStay).filter(ICUStay.hadm_id == adm.hadm_id).all()
        risk      = db.query(RiskScore).filter(RiskScore.hadm_id == adm.hadm_id)\
                      .order_by(RiskScore.calculated_at.desc()).first()
        alerts    = db.query(Alert).filter(Alert.hadm_id == adm.hadm_id).all()

        adm_data = {
            "hadm_id":        adm.hadm_id,
            "admission_type": adm.admission_type,
            "admittime":      adm.admittime,
            "dischtime":      adm.dischtime,
            "hospital_los":   adm.hospital_los,
            "diagnosis":      adm.diagnosis,
            "insurance":      adm.insurance,
            "marital_status": adm.marital_status,
            "ethnicity":      adm.ethnicity,
            "risk": {
                "score":                risk.score,
                "risk_level":           risk.risk_level,
                "contributing_factors": json.loads(risk.contributing_factors)
                                        if risk and risk.contributing_factors else [],
            } if risk else None,
            "alerts": [
                {
                    "id": a.id, "type": a.alert_type, "severity": a.severity,
                    "message": a.message, "indicator": a.indicator,
                    "value": a.value, "acknowledged": a.is_acknowledged,
                    "created_at": str(a.created_at)
                }
                for a in alerts
            ],
            "icu_stays": []
        }

        for icu in icu_stays:
            adm_data["icu_stays"].append({
                "icustay_id":    icu.icustay_id,
                "first_careunit": icu.first_careunit,
                "los":           icu.los,
                "vitals": {
                    "heart_rate":   {"mean": icu.heart_rate_mean,    "min": icu.heart_rate_min,    "max": icu.heart_rate_max},
                    "resp_rate":    {"mean": icu.resp_rate_mean,     "min": icu.resp_rate_min,     "max": icu.resp_rate_max},
                    "spo2":         {"mean": icu.spo2_mean,          "min": icu.spo2_min,          "max": icu.spo2_max},
                    "bp_systolic":  {"mean": icu.bp_systolic_mean,   "min": icu.bp_systolic_min,   "max": icu.bp_systolic_max},
                    "bp_diastolic": {"mean": icu.bp_diastolic_mean,  "min": icu.bp_diastolic_min,  "max": icu.bp_diastolic_max},
                },
                "labs": {
                    "creatinine": {"mean": icu.creatinine_mean, "max": icu.creatinine_max},
                    "glucose":    {"mean": icu.glucose_mean,    "max": icu.glucose_max},
                    "hemoglobin": {"mean": icu.hemoglobin_mean, "min": icu.hemoglobin_min},
                    "potassium":  {"mean": icu.potassium_mean},
                    "sodium":     {"mean": icu.sodium_mean},
                    "wbc":        {"mean": icu.wbc_mean,        "max": icu.wbc_max},
                }
            })

        result["admissions"].append(adm_data)

    return result


@router.get("/{subject_id}/timeline")
def get_patient_timeline(
    subject_id:   int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    patient = db.query(Patient).filter(Patient.subject_id == subject_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    admissions = db.query(Admission).filter(Admission.subject_id == subject_id)\
                   .order_by(Admission.admittime).all()
    events = []

    for adm in admissions:
        events.append({
            "type": "admission", "date": adm.admittime,
            "title": f"Hospital Admission ({adm.admission_type})",
            "detail": adm.diagnosis, "hadm_id": adm.hadm_id
        })

        for icu in db.query(ICUStay).filter(ICUStay.hadm_id == adm.hadm_id).all():
            events.append({
                "type": "icu_admission", "date": icu.intime or adm.admittime,
                "title": f"ICU Admission — {icu.first_careunit}",
                "detail": f"LOS: {icu.los:.1f} days" if icu.los else "",
                "icustay_id": icu.icustay_id
            })

        risk = db.query(RiskScore).filter(RiskScore.hadm_id == adm.hadm_id).first()
        if risk:
            events.append({
                "type": f"risk_{risk.risk_level.lower()}", "date": adm.admittime,
                "title": f"Risk Assessment: {risk.risk_level}",
                "detail": f"Score: {risk.score}/100",
                "score": risk.score, "risk_level": risk.risk_level
            })

        for alert in db.query(Alert).filter(Alert.hadm_id == adm.hadm_id, Alert.severity == "critical").all():
            events.append({
                "type": "alert_critical", "date": str(alert.created_at),
                "title": "Critical Alert", "detail": alert.message
            })

        if adm.dischtime:
            events.append({
                "type": "discharge", "date": adm.dischtime,
                "title": "Hospital Discharge",
                "detail": f"LOS: {adm.hospital_los:.1f} days" if adm.hospital_los else ""
            })

    events.sort(key=lambda x: x.get("date") or "")
    return {"subject_id": subject_id, "events": events}
