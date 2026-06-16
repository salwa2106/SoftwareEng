export interface PatientSummary {
  subject_id: number;
  gender: string | null;
  age: number | null;
  icu_stays: number;
  los_hours: number | null;
  diagnosis: string | null;
  ethnicity: string | null;
  current_risk: string;
}

export interface PatientDetail {
  subject_id: number;
  gender: string | null;
  age: number | null;
  diagnosis: string | null;
  ethnicity: string | null;
  admittime: string | null;
  dischtime: string | null;
  icu_intime: string | null;
  icu_outtime: string | null;
  los_hours: number | null;
  icu_unit: string | null;
}

export interface HourlyFeatures {
  hour: number;
  timestamp: string;
  heart_rate: number | null;
  resp_rate: number | null;
  spo2: number | null;
  temperature: number | null;
  sbp: number | null;
  dbp: number | null;
  wbc: number | null;
  creatinine: number | null;
  lactate: number | null;
  hemoglobin: number | null;
  platelets: number | null;
  abnormal_count: number;
  risk_score: string;
  risk_value: number;
  triggers: string[];
  events: Array<{ type: string; count: number; label: string }>;
}

export interface TimelineResponse {
  subject_id: number;
  icu_intime: string;
  icu_outtime: string | null;
  total_hours: number;
  hourly_data: HourlyFeatures[];
}

export interface RiskScore {
  subject_id: number;
  timestamp: string;
  risk_level: string;
  risk_value: number;
  abnormal_values: Record<string, number>;
  trend: string;
  triggers: string[];
}

export interface Alert {
  alert_id: string;
  subject_id: number;
  hour: number;
  timestamp: string;
  severity: string;
  triggers: string[];
  risk_before: string;
  risk_after: string;
  details: Record<string, number | null>;
}

export interface AlertsResponse {
  subject_id: number;
  total_alerts: number;
  alerts: Alert[];
}

export interface PatientsResponse {
  total: number;
  offset: number;
  limit: number;
  patients: PatientSummary[];
}

export interface HealthResponse {
  status: string;
  data_loaded: boolean;
  patient_count: number;
  message: string;
}
