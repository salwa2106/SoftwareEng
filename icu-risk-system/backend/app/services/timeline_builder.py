import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import logging
from app.config import settings
from app.services.data_loader import data_loader
from app.utils.helpers import safe_float, calculate_age, hours_between

logger = logging.getLogger(__name__)

class TimelineBuilder:
    """Reconstructs ICU stay hour-by-hour for a patient."""

    def build_timeline(self, subject_id: int) -> Optional[Dict]:
        """Build complete hourly timeline for a patient ICU stay."""
        icustays = data_loader.get_icustays()
        if icustays is None:
            return None

        subj_col = settings.ICUSTAYS_SUBJECT_COL.lower()
        intime_col = settings.ICUSTAYS_INTIME_COL.lower()
        outtime_col = settings.ICUSTAYS_OUTTIME_COL.lower()

        patient_stays = icustays[icustays[subj_col] == subject_id]
        if patient_stays.empty:
            return None

        stay = patient_stays.sort_values(intime_col).iloc[0]
        icu_intime = pd.to_datetime(stay[intime_col])
        icu_outtime_raw = stay.get(outtime_col)
        icu_outtime = pd.to_datetime(icu_outtime_raw) if (icu_outtime_raw is not None and str(icu_outtime_raw) not in ['', 'nan', 'NaT']) else None

        chart_data = self._get_chart_data(subject_id, icu_intime, icu_outtime)
        lab_data = self._get_lab_data(subject_id, icu_intime, icu_outtime)
        med_data = self._get_med_data(subject_id)
        proc_data = self._get_proc_data(subject_id)

        if icu_outtime:
            total_hours = max(1, int((icu_outtime - icu_intime).total_seconds() / 3600))
        else:
            total_hours = 72

        total_hours = min(total_hours, 336)

        hourly_data = []
        prev_features = {}

        for hour in range(total_hours):
            slot_start = icu_intime + timedelta(hours=hour)
            slot_end = slot_start + timedelta(hours=1)

            features = self._extract_features_for_hour(
                hour, slot_start, slot_end,
                chart_data, lab_data, med_data, proc_data,
                prev_features
            )
            hourly_data.append(features)
            prev_features = features

        return {
            "subject_id": subject_id,
            "icu_intime": icu_intime.isoformat(),
            "icu_outtime": icu_outtime.isoformat() if icu_outtime else None,
            "total_hours": total_hours,
            "hourly_data": hourly_data
        }

    def _get_chart_data(self, subject_id: int, start, end) -> Optional[pd.DataFrame]:
        charts = data_loader.get_chartevents()
        if charts is None:
            return None
        subj_col = settings.CHART_SUBJECT_COL.lower()
        time_col = settings.CHART_TIME_COL.lower()

        df = charts[charts[subj_col] == subject_id].copy()
        if df.empty:
            return None
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        if end:
            df = df[(df[time_col] >= start) & (df[time_col] <= end)]
        return df if not df.empty else None

    def _get_lab_data(self, subject_id: int, start, end) -> Optional[pd.DataFrame]:
        labs = data_loader.get_labevents()
        if labs is None:
            return None
        subj_col = settings.LAB_SUBJECT_COL.lower()
        time_col = settings.LAB_TIME_COL.lower()

        df = labs[labs[subj_col] == subject_id].copy()
        if df.empty:
            return None
        df[time_col] = pd.to_datetime(df[time_col], errors='coerce')
        if end:
            df = df[(df[time_col] >= start) & (df[time_col] <= end)]
        return df if not df.empty else None

    def _get_med_data(self, subject_id: int) -> Optional[pd.DataFrame]:
        meds = data_loader.get_prescriptions()
        if meds is None:
            return None
        subj_col = settings.PRESC_SUBJECT_COL.lower()
        df = meds[meds[subj_col] == subject_id]
        return df if not df.empty else None

    def _get_proc_data(self, subject_id: int) -> Optional[pd.DataFrame]:
        procs = data_loader.get_procedures()
        if procs is None:
            return None
        subj_col = settings.PROC_SUBJECT_COL.lower()
        df = procs[procs[subj_col] == subject_id]
        return df if not df.empty else None

    def _get_latest_value(self, df: pd.DataFrame, item_ids: list, time_col: str, val_col: str, itemid_col: str, slot_end) -> Optional[float]:
        if df is None:
            return None
        try:
            mask = (df[itemid_col].isin(item_ids)) & (df[time_col] <= slot_end)
            sub = df[mask]
            if sub.empty:
                return None
            latest = sub.sort_values(time_col).iloc[-1]
            return safe_float(latest[val_col])
        except Exception:
            return None

    def _extract_features_for_hour(self, hour: int, slot_start, slot_end, chart_data, lab_data, med_data, proc_data, prev: dict) -> dict:
        itemid_col = "itemid"

        def chart_val(items):
            return self._get_latest_value(
                chart_data, items,
                settings.CHART_TIME_COL.lower(),
                settings.CHART_VALUE_COL.lower(),
                itemid_col, slot_end
            )

        def lab_val(items):
            return self._get_latest_value(
                lab_data, items,
                settings.LAB_TIME_COL.lower(),
                settings.LAB_VALUE_COL.lower(),
                itemid_col, slot_end
            )

        hr = chart_val(settings.HEART_RATE_ITEMS)
        rr = chart_val(settings.RESP_RATE_ITEMS)
        spo2 = chart_val(settings.SPO2_ITEMS)
        temp = chart_val(settings.TEMPERATURE_ITEMS)
        sbp = chart_val(settings.SBP_ITEMS)
        dbp = chart_val(settings.DBP_ITEMS)
        wbc = lab_val(settings.WBC_ITEMS)
        creatinine = lab_val(settings.CREATININE_ITEMS)
        lactate = lab_val(settings.LACTATE_ITEMS)
        hemoglobin = lab_val(settings.HEMOGLOBIN_ITEMS)
        platelets = lab_val(settings.PLATELETS_ITEMS)

        events = self._collect_hour_events(slot_start, slot_end, chart_data, lab_data, med_data, proc_data)
        abnormal = self._count_abnormals(hr, rr, spo2, temp, wbc, creatinine, lactate, hemoglobin, platelets)

        return {
            "hour": hour,
            "timestamp": slot_start.isoformat(),
            "heart_rate": hr,
            "resp_rate": rr,
            "spo2": spo2,
            "temperature": temp,
            "sbp": sbp,
            "dbp": dbp,
            "wbc": wbc,
            "creatinine": creatinine,
            "lactate": lactate,
            "hemoglobin": hemoglobin,
            "platelets": platelets,
            "abnormal_count": abnormal,
            "events": events
        }

    def _count_abnormals(self, hr, rr, spo2, temp, wbc, creatinine, lactate, hemoglobin, platelets) -> int:
        count = 0
        if hr is not None and (hr < settings.HEART_RATE_LOW or hr > settings.HEART_RATE_HIGH):
            count += 1
        if rr is not None and (rr < settings.RESP_RATE_LOW or rr > settings.RESP_RATE_HIGH):
            count += 1
        if spo2 is not None and spo2 < settings.SPO2_LOW:
            count += 1
        if temp is not None and (temp < settings.TEMP_LOW or temp > settings.TEMP_HIGH):
            count += 1
        if wbc is not None and (wbc < settings.WBC_LOW or wbc > settings.WBC_HIGH):
            count += 1
        if creatinine is not None and creatinine > settings.CREATININE_HIGH:
            count += 1
        if lactate is not None and lactate > settings.LACTATE_HIGH:
            count += 1
        if hemoglobin is not None and hemoglobin < settings.HEMOGLOBIN_LOW:
            count += 1
        if platelets is not None and platelets < settings.PLATELETS_LOW:
            count += 1
        return count

    def _collect_hour_events(self, slot_start, slot_end, chart_data, lab_data, med_data, proc_data) -> list:
        events = []

        try:
            if chart_data is not None:
                time_col = settings.CHART_TIME_COL.lower()
                mask = (chart_data[time_col] >= slot_start) & (chart_data[time_col] < slot_end)
                hour_charts = chart_data[mask]
                if not hour_charts.empty:
                    events.append({
                        "type": "vitals",
                        "count": len(hour_charts),
                        "label": f"{len(hour_charts)} vital sign readings"
                    })
        except Exception:
            pass

        try:
            if lab_data is not None:
                time_col = settings.LAB_TIME_COL.lower()
                mask = (lab_data[time_col] >= slot_start) & (lab_data[time_col] < slot_end)
                hour_labs = lab_data[mask]
                if not hour_labs.empty:
                    events.append({
                        "type": "lab",
                        "count": len(hour_labs),
                        "label": f"{len(hour_labs)} lab results"
                    })
        except Exception:
            pass

        try:
            if med_data is not None:
                start_col = settings.PRESC_STARTDATE_COL.lower()
                if start_col in med_data.columns:
                    med_times = pd.to_datetime(med_data[start_col], errors='coerce')
                    mask = (med_times >= slot_start) & (med_times < slot_end)
                    hour_meds = med_data[mask]
                    if not hour_meds.empty:
                        drug_col = settings.PRESC_DRUG_COL.lower()
                        drugs = hour_meds[drug_col].dropna().unique()[:3].tolist() if drug_col in hour_meds.columns else []
                        events.append({
                            "type": "medication",
                            "count": len(hour_meds),
                            "label": f"Medications: {', '.join(str(d) for d in drugs)}" if drugs else f"{len(hour_meds)} medications"
                        })
        except Exception:
            pass

        return events

timeline_builder = TimelineBuilder()
