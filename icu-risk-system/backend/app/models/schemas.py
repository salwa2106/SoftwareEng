from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class PatientSummary(BaseModel):
    subject_id: int
    gender: Optional[str] = None
    age: Optional[int] = None
    icu_stays: int = 0
    los_hours: Optional[float] = None
    diagnosis: Optional[str] = None
    ethnicity: Optional[str] = None
    current_risk: Optional[str] = "Unknown"

class PatientDetail(BaseModel):
    subject_id: int
    gender: Optional[str] = None
    age: Optional[int] = None
    diagnosis: Optional[str] = None
    ethnicity: Optional[str] = None
    admittime: Optional[str] = None
    dischtime: Optional[str] = None
    icu_intime: Optional[str] = None
    icu_outtime: Optional[str] = None
    los_hours: Optional[float] = None
    icu_unit: Optional[str] = None

class HourlyFeatures(BaseModel):
    hour: int
    timestamp: str
    heart_rate: Optional[float] = None
    resp_rate: Optional[float] = None
    spo2: Optional[float] = None
    temperature: Optional[float] = None
    sbp: Optional[float] = None
    dbp: Optional[float] = None
    wbc: Optional[float] = None
    creatinine: Optional[float] = None
    lactate: Optional[float] = None
    hemoglobin: Optional[float] = None
    platelets: Optional[float] = None
    abnormal_count: int = 0
    risk_score: str = "Low"
    events: List[Dict[str, Any]] = []

class TimelineResponse(BaseModel):
    subject_id: int
    icu_intime: str
    icu_outtime: Optional[str] = None
    total_hours: int
    hourly_data: List[HourlyFeatures]

class RiskScore(BaseModel):
    subject_id: int
    timestamp: str
    risk_level: str
    risk_value: float
    abnormal_values: Dict[str, Any]
    trend: str

class Alert(BaseModel):
    alert_id: str
    subject_id: int
    hour: int
    timestamp: str
    severity: str
    triggers: List[str]
    risk_before: str
    risk_after: str
    details: Dict[str, Any]

class AlertsResponse(BaseModel):
    subject_id: int
    total_alerts: int
    alerts: List[Alert]

class HealthResponse(BaseModel):
    status: str
    data_loaded: bool
    patient_count: int
    message: str
