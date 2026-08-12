"""
Dataset loader: reads the cleaned MIMIC-III CSV and populates the SQLite database.
Matched to final_icu_dataset.csv column names.
"""

import pandas as pd
import numpy as np
import json
import os
from sqlalchemy.orm import Session
from app.models.user import Patient, Admission, ICUStay, RiskScore, Alert
from app.ml.risk_engine import calculate_risk_score
from app.core.security import get_password_hash


def _safe_float(val, default=None):
    try:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def load_dataset(db: Session, csv_path: str, limit: int = None) -> dict:
    """
    Load cleaned MIMIC-III CSV into the database.
    Column names matched to final_icu_dataset.csv
    """
    if not os.path.exists(csv_path):
        return {"error": f"CSV file not found at: {csv_path}"}

    print(f"Loading dataset from {csv_path}...")
    df = pd.read_csv(csv_path, low_memory=False)

    if limit:
        df = df.head(limit)

    print(f"Total rows to load: {len(df)}")

    loaded = {"patients": 0, "admissions": 0, "icustays": 0, "risk_scores": 0, "alerts": 0}
    seen_subjects = set()
    seen_hadm = set()
    seen_icu = set()

    for idx, row in df.iterrows():
        subject_id  = int(row['SUBJECT_ID'])
        hadm_id     = int(row['HADM_ID'])
        icustay_id  = int(row['ICUSTAY_ID'])

        # ── Patient ──────────────────────────────────────────────────
        if subject_id not in seen_subjects:
            if not db.query(Patient).filter_by(subject_id=subject_id).first():
                db.add(Patient(
                    subject_id=subject_id,
                    gender=str(row.get('GENDER', 'Unknown')).strip(),
                    age=_safe_float(row.get('AGE')),
                ))
                loaded["patients"] += 1
            seen_subjects.add(subject_id)

        # ── Admission ─────────────────────────────────────────────────
        if hadm_id not in seen_hadm:
            if not db.query(Admission).filter_by(hadm_id=hadm_id).first():
                db.add(Admission(
                    hadm_id=hadm_id,
                    subject_id=subject_id,
                    admission_type=str(row.get('ADMISSION_TYPE', 'UNKNOWN')),
                    admittime=str(row.get('INTIME', '')),
                    dischtime=str(row.get('OUTTIME', '')),
                    hospital_los=_safe_float(row.get('HOSPITAL_LOS_DAYS')),
                    diagnosis='',
                    insurance='',
                    marital_status='',
                    ethnicity='',
                ))
                loaded["admissions"] += 1
            seen_hadm.add(hadm_id)

        # ── ICU Stay ──────────────────────────────────────────────────
        if icustay_id not in seen_icu:
            if not db.query(ICUStay).filter_by(icustay_id=icustay_id).first():
                icu = ICUStay(
                    icustay_id=icustay_id,
                    hadm_id=hadm_id,
                    subject_id=subject_id,
                    first_careunit=str(row.get('FIRST_CAREUNIT', 'ICU')),
                    last_careunit=str(row.get('LAST_CAREUNIT', '')),
                    intime=str(row.get('INTIME', '')),
                    outtime=str(row.get('OUTTIME', '')),
                    los=_safe_float(row.get('LOS')),
                    # Vitals
                    heart_rate_mean=_safe_float(row.get('HeartRate_mean')),
                    heart_rate_min =_safe_float(row.get('HeartRate_min')),
                    heart_rate_max =_safe_float(row.get('HeartRate_max')),
                    resp_rate_mean =_safe_float(row.get('RespiratoryRate_mean')),
                    resp_rate_min  =_safe_float(row.get('RespiratoryRate_min')),
                    resp_rate_max  =_safe_float(row.get('RespiratoryRate_max')),
                    spo2_mean      =_safe_float(row.get('SpO2_mean')),
                    spo2_min       =_safe_float(row.get('SpO2_min')),
                    spo2_max       =_safe_float(row.get('SpO2_max')),
                    bp_systolic_mean =_safe_float(row.get('SystolicBP_mean')),
                    bp_systolic_min  =_safe_float(row.get('SystolicBP_min')),
                    bp_systolic_max  =_safe_float(row.get('SystolicBP_max')),
                    bp_diastolic_mean=_safe_float(row.get('DiastolicBP_mean')),
                    bp_diastolic_min =_safe_float(row.get('DiastolicBP_min')),
                    bp_diastolic_max =_safe_float(row.get('DiastolicBP_max')),
                    # Labs
                    creatinine_mean=_safe_float(row.get('Creatinine_mean')),
                    creatinine_max =_safe_float(row.get('Creatinine_max')),
                    glucose_mean   =_safe_float(row.get('Glucose_mean')),
                    glucose_max    =_safe_float(row.get('Glucose_max')),
                    hemoglobin_mean=_safe_float(row.get('Hemoglobin_mean')),
                    hemoglobin_min =_safe_float(row.get('Hemoglobin_max')),
                    potassium_mean =_safe_float(row.get('Potassium_mean')),
                    sodium_mean    =_safe_float(row.get('Sodium_mean')),
                    wbc_mean       =_safe_float(row.get('WBC_mean')),
                    wbc_max        =_safe_float(row.get('WBC_max')),
                )
                db.add(icu)
                loaded["icustays"] += 1

                # ── Risk Score ────────────────────────────────────────
                risk_input = {
                    "heart_rate":   icu.heart_rate_mean,
                    "resp_rate":    icu.resp_rate_mean,
                    "spo2":         icu.spo2_mean,
                    "bp_systolic":  icu.bp_systolic_mean,
                    "bp_diastolic": icu.bp_diastolic_mean,
                    "creatinine":   icu.creatinine_mean,
                    "glucose":      icu.glucose_mean,
                    "hemoglobin":   icu.hemoglobin_mean,
                    "potassium":    icu.potassium_mean,
                    "sodium":       icu.sodium_mean,
                    "wbc":          icu.wbc_mean,
                    "icu_los":      icu.los,
                }
                result = calculate_risk_score(risk_input)

                db.add(RiskScore(
                    hadm_id=hadm_id,
                    icustay_id=icustay_id,
                    score=result["score"],
                    risk_level=result["risk_level"],
                    contributing_factors=json.dumps(result["contributing_factors"]),
                ))
                loaded["risk_scores"] += 1

                for alert_info in result["alerts"]:
                    db.add(Alert(
                        hadm_id=hadm_id,
                        icustay_id=icustay_id,
                        alert_type=alert_info["type"],
                        severity=alert_info["severity"],
                        message=alert_info["message"],
                        indicator=alert_info["indicator"],
                        value=alert_info.get("value"),
                        threshold=0,
                    ))
                    loaded["alerts"] += 1

            seen_icu.add(icustay_id)

        # Commit every 500 rows
        if idx % 500 == 0:
            db.commit()
            print(f"  Processed {idx}/{len(df)} rows...")

    db.commit()
    print(f"Dataset load complete: {loaded}")
    return loaded


def seed_default_user(db: Session):
    from app.models.user import User
    if not db.query(User).filter_by(username="admin").first():
        db.add(User(
            username="admin",
            email="admin@pulseguardian.icu",
            hashed_password=get_password_hash("admin123"),
            full_name="System Administrator",
            role="admin",
        ))
        db.commit()
        print("Default admin user created: admin / admin123")


def generate_synthetic_data(db: Session, n: int = 200):
    import random
    random.seed(42)
    np.random.seed(42)

    admission_types = ["EMERGENCY", "ELECTIVE", "URGENT"]
    care_units = ["MICU", "SICU", "CCU", "CSRU", "TSICU"]
    genders = ["M", "F"]

    loaded = {"patients": 0, "admissions": 0, "icustays": 0, "risk_scores": 0, "alerts": 0}

    for i in range(n):
        subject_id = 10000 + i
        hadm_id    = 200000 + i
        icustay_id = 300000 + i

        is_high = random.random() < 0.30
        is_med  = random.random() < 0.35

        if is_high:
            hr=np.random.normal(115,20); rr=np.random.normal(26,5); spo2=np.random.normal(90,4)
            sbp=np.random.normal(85,15); dbp=np.random.normal(50,10); crea=np.random.normal(2.5,1)
            gluc=np.random.normal(180,40); hgb=np.random.normal(9,1.5); k=np.random.normal(5.5,0.8)
            na=np.random.normal(148,5); wbc=np.random.normal(15,4); los=np.random.exponential(10)
        elif is_med:
            hr=np.random.normal(95,15); rr=np.random.normal(21,4); spo2=np.random.normal(94,3)
            sbp=np.random.normal(100,15); dbp=np.random.normal(65,10); crea=np.random.normal(1.5,0.5)
            gluc=np.random.normal(130,30); hgb=np.random.normal(11,1.5); k=np.random.normal(4.8,0.6)
            na=np.random.normal(140,4); wbc=np.random.normal(11,3); los=np.random.exponential(5)
        else:
            hr=np.random.normal(78,10); rr=np.random.normal(16,2); spo2=np.random.normal(97,1.5)
            sbp=np.random.normal(120,10); dbp=np.random.normal(75,8); crea=np.random.normal(0.9,0.2)
            gluc=np.random.normal(100,15); hgb=np.random.normal(13.5,1.5); k=np.random.normal(4.0,0.4)
            na=np.random.normal(140,3); wbc=np.random.normal(8,2); los=np.random.exponential(2.5)

        db.add(Patient(subject_id=subject_id, gender=random.choice(genders), age=round(np.random.normal(62,16))))
        db.add(Admission(hadm_id=hadm_id, subject_id=subject_id,
            admission_type=random.choice(admission_types),
            admittime="2150-01-01 08:00:00", dischtime="2150-01-15 10:00:00",
            hospital_los=round(los+random.uniform(1,5),1), diagnosis="ICU ADMISSION",
            insurance="Medicare", marital_status="MARRIED", ethnicity="WHITE"))

        icu = ICUStay(
            icustay_id=icustay_id, hadm_id=hadm_id, subject_id=subject_id,
            first_careunit=random.choice(care_units), los=round(max(0.5,los),1),
            heart_rate_mean=max(30,hr), heart_rate_min=max(30,hr-15), heart_rate_max=min(200,hr+15),
            resp_rate_mean=max(5,rr), resp_rate_min=max(5,rr-4), resp_rate_max=min(50,rr+4),
            spo2_mean=min(100,max(70,spo2)), spo2_min=min(100,max(70,spo2-5)), spo2_max=min(100,spo2+2),
            bp_systolic_mean=max(50,sbp), bp_systolic_min=max(50,sbp-20), bp_systolic_max=min(220,sbp+20),
            bp_diastolic_mean=max(30,dbp), bp_diastolic_min=max(30,dbp-15), bp_diastolic_max=min(130,dbp+15),
            creatinine_mean=max(0.3,crea), creatinine_max=max(0.3,crea+0.5),
            glucose_mean=max(40,gluc), glucose_max=max(40,gluc+30),
            hemoglobin_mean=max(5,hgb), hemoglobin_min=max(5,hgb-1.5),
            potassium_mean=max(2,k), sodium_mean=max(120,na),
            wbc_mean=max(1,wbc), wbc_max=max(1,wbc+3),
        )
        db.add(icu)

        risk_input = {
            "heart_rate": icu.heart_rate_mean, "resp_rate": icu.resp_rate_mean,
            "spo2": icu.spo2_mean, "bp_systolic": icu.bp_systolic_mean,
            "bp_diastolic": icu.bp_diastolic_mean, "creatinine": icu.creatinine_mean,
            "glucose": icu.glucose_mean, "hemoglobin": icu.hemoglobin_mean,
            "potassium": icu.potassium_mean, "sodium": icu.sodium_mean,
            "wbc": icu.wbc_mean, "icu_los": icu.los,
        }
        result = calculate_risk_score(risk_input)

        db.add(RiskScore(hadm_id=hadm_id, icustay_id=icustay_id,
            score=result["score"], risk_level=result["risk_level"],
            contributing_factors=json.dumps(result["contributing_factors"])))

        for a in result["alerts"]:
            db.add(Alert(hadm_id=hadm_id, icustay_id=icustay_id,
                alert_type=a["type"], severity=a["severity"],
                message=a["message"], indicator=a["indicator"],
                value=a.get("value"), threshold=0))

        loaded["patients"] += 1; loaded["admissions"] += 1
        loaded["icustays"] += 1; loaded["risk_scores"] += 1
        loaded["alerts"] += len(result["alerts"])

    db.commit()
    print(f"Synthetic data generated: {loaded}")
    return loaded
