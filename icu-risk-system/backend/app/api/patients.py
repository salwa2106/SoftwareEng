from fastapi import APIRouter, HTTPException
from typing import List
import pandas as pd
from app.services.data_loader import data_loader
from app.services.timeline_builder import timeline_builder
from app.services.risk_engine import risk_engine
from app.config import settings
from app.utils.helpers import calculate_age, normalize_gender, hours_between

router = APIRouter()

@router.get("/patients")
def list_patients(limit: int = 50, offset: int = 0, search: str = ""):
    """Return paginated list of patients with basic info."""
    patients_df = data_loader.get_patients()
    admissions_df = data_loader.get_admissions()
    icustays_df = data_loader.get_icustays()

    if patients_df is None:
        raise HTTPException(status_code=503, detail="Patient data not available")

    pid_col = settings.PATIENTS_ID_COL.lower()
    gender_col = settings.PATIENTS_GENDER_COL.lower()
    dob_col = settings.PATIENTS_DOB_COL.lower()

    results = []
    patient_ids = patients_df[pid_col].unique().tolist()

    for pid in patient_ids[offset:offset+limit]:
        row = patients_df[patients_df[pid_col] == pid].iloc[0]

        gender = normalize_gender(row.get(gender_col, "")) if gender_col in patients_df.columns else "Unknown"

        age = None
        if dob_col in patients_df.columns and admissions_df is not None:
            admit_col = settings.ADMISSIONS_ADMIT_COL.lower()
            subj_col = settings.ADMISSIONS_SUBJECT_COL.lower()
            adm = admissions_df[admissions_df[subj_col] == pid]
            if not adm.empty and admit_col in adm.columns:
                first_admit = adm.sort_values(admit_col).iloc[0][admit_col]
                age = calculate_age(str(row[dob_col]), str(first_admit))

        los_hours = None
        icu_stays = 0
        if icustays_df is not None:
            ist_subj_col = settings.ICUSTAYS_SUBJECT_COL.lower()
            stays = icustays_df[icustays_df[ist_subj_col] == pid]
            icu_stays = len(stays)
            los_col = settings.ICUSTAYS_LOS_COL.lower()
            if not stays.empty and los_col in stays.columns:
                los_val = stays[los_col].sum()
                los_hours = round(float(los_val) * 24, 1) if los_val else None

        diagnosis = None
        if admissions_df is not None:
            diag_col = settings.ADMISSIONS_DIAGNOSIS_COL.lower()
            subj_col = settings.ADMISSIONS_SUBJECT_COL.lower()
            adm = admissions_df[admissions_df[subj_col] == pid]
            if not adm.empty and diag_col in adm.columns:
                diagnosis = str(adm.iloc[0][diag_col])[:80]

        results.append({
            "subject_id": int(pid),
            "gender": gender,
            "age": age,
            "icu_stays": icu_stays,
            "los_hours": los_hours,
            "diagnosis": diagnosis,
            "current_risk": "Unknown",
            "ethnicity": None
        })

    # Filter by search if provided
    if search:
        search_lower = search.lower()
        results = [r for r in results if
                   search_lower in str(r["subject_id"]) or
                   (r["diagnosis"] and search_lower in r["diagnosis"].lower())]

    return {
        "total": len(patient_ids),
        "offset": offset,
        "limit": limit,
        "patients": results
    }

@router.get("/patients/{patient_id}")
def get_patient(patient_id: int):
    """Return detailed info for one patient."""
    patients_df = data_loader.get_patients()
    if patients_df is None:
        raise HTTPException(status_code=503, detail="Data not available")

    pid_col = settings.PATIENTS_ID_COL.lower()
    rows = patients_df[patients_df[pid_col] == patient_id]
    if rows.empty:
        raise HTTPException(status_code=404, detail=f"Patient {patient_id} not found")

    row = rows.iloc[0]
    gender_col = settings.PATIENTS_GENDER_COL.lower()
    dob_col = settings.PATIENTS_DOB_COL.lower()

    gender = normalize_gender(row.get(gender_col, "")) if gender_col in patients_df.columns else "Unknown"

    admissions_df = data_loader.get_admissions()
    diagnosis = None
    admittime = None
    dischtime = None
    ethnicity = None
    age = None

    if admissions_df is not None:
        subj_col = settings.ADMISSIONS_SUBJECT_COL.lower()
        adm = admissions_df[admissions_df[subj_col] == patient_id]
        if not adm.empty:
            first_adm = adm.sort_values(settings.ADMISSIONS_ADMIT_COL.lower()).iloc[0]
            diag_col = settings.ADMISSIONS_DIAGNOSIS_COL.lower()
            admit_col = settings.ADMISSIONS_ADMIT_COL.lower()
            disch_col = settings.ADMISSIONS_DISCH_COL.lower()
            eth_col = settings.ADMISSIONS_ETHNICITY_COL.lower()

            if diag_col in adm.columns:
                diagnosis = str(first_adm.get(diag_col, ""))
            if admit_col in adm.columns:
                admittime = str(first_adm.get(admit_col, ""))
                if dob_col in patients_df.columns:
                    age = calculate_age(str(row.get(dob_col, "")), admittime)
            if disch_col in adm.columns:
                dischtime = str(first_adm.get(disch_col, ""))
            if eth_col in adm.columns:
                ethnicity = str(first_adm.get(eth_col, ""))

    icustays_df = data_loader.get_icustays()
    icu_intime = None
    icu_outtime = None
    los_hours = None
    icu_unit = None

    if icustays_df is not None:
        ist_subj_col = settings.ICUSTAYS_SUBJECT_COL.lower()
        stays = icustays_df[icustays_df[ist_subj_col] == patient_id]
        if not stays.empty:
            stay = stays.sort_values(settings.ICUSTAYS_INTIME_COL.lower()).iloc[0]
            intime_col = settings.ICUSTAYS_INTIME_COL.lower()
            outtime_col = settings.ICUSTAYS_OUTTIME_COL.lower()
            los_col = settings.ICUSTAYS_LOS_COL.lower()
            unit_col = settings.ICUSTAYS_UNIT_COL.lower()

            if intime_col in stays.columns:
                icu_intime = str(stay.get(intime_col, ""))
            if outtime_col in stays.columns:
                icu_outtime = str(stay.get(outtime_col, ""))
            if los_col in stays.columns:
                los_val = stay.get(los_col)
                los_hours = round(float(los_val) * 24, 1) if los_val else None
            if unit_col in stays.columns:
                icu_unit = str(stay.get(unit_col, ""))

    return {
        "subject_id": patient_id,
        "gender": gender,
        "age": age,
        "diagnosis": diagnosis,
        "ethnicity": ethnicity,
        "admittime": admittime,
        "dischtime": dischtime,
        "icu_intime": icu_intime,
        "icu_outtime": icu_outtime,
        "los_hours": los_hours,
        "icu_unit": icu_unit
    }
