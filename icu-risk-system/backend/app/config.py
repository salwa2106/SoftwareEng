from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    DATA_DIR: str = str(BASE_DIR / "data")
    USE_SAMPLE_DATA: bool = True
    SAMPLE_DATA_DIR: str = str(BASE_DIR / "data" / "sample")

    PATIENTS_ID_COL: str = "subject_id"
    PATIENTS_GENDER_COL: str = "gender"
    PATIENTS_DOB_COL: str = "dob"
    PATIENTS_DOD_COL: str = "dod"

    ADMISSIONS_ID_COL: str = "hadm_id"
    ADMISSIONS_SUBJECT_COL: str = "subject_id"
    ADMISSIONS_ADMIT_COL: str = "admittime"
    ADMISSIONS_DISCH_COL: str = "dischtime"
    ADMISSIONS_DIAGNOSIS_COL: str = "diagnosis"
    ADMISSIONS_ETHNICITY_COL: str = "ethnicity"

    ICUSTAYS_ID_COL: str = "icustay_id"
    ICUSTAYS_SUBJECT_COL: str = "subject_id"
    ICUSTAYS_HADM_COL: str = "hadm_id"
    ICUSTAYS_INTIME_COL: str = "intime"
    ICUSTAYS_OUTTIME_COL: str = "outtime"
    ICUSTAYS_LOS_COL: str = "los"
    ICUSTAYS_UNIT_COL: str = "first_careunit"

    CHART_SUBJECT_COL: str = "subject_id"
    CHART_HADM_COL: str = "hadm_id"
    CHART_ICUSTAY_COL: str = "icustay_id"
    CHART_ITEMID_COL: str = "itemid"
    CHART_TIME_COL: str = "charttime"
    CHART_VALUE_COL: str = "valuenum"
    CHART_VALUEUOM_COL: str = "valueuom"

    LAB_SUBJECT_COL: str = "subject_id"
    LAB_HADM_COL: str = "hadm_id"
    LAB_ITEMID_COL: str = "itemid"
    LAB_TIME_COL: str = "charttime"
    LAB_VALUE_COL: str = "valuenum"
    LAB_VALUEUOM_COL: str = "valueuom"

    PRESC_SUBJECT_COL: str = "subject_id"
    PRESC_HADM_COL: str = "hadm_id"
    PRESC_ICUSTAY_COL: str = "icustay_id"
    PRESC_STARTDATE_COL: str = "startdate"
    PRESC_ENDDATE_COL: str = "enddate"
    PRESC_DRUG_COL: str = "drug"
    PRESC_DOSE_COL: str = "dose_val_rx"
    PRESC_UNIT_COL: str = "dose_unit_rx"

    PROC_SUBJECT_COL: str = "subject_id"
    PROC_HADM_COL: str = "hadm_id"
    PROC_ICUSTAY_COL: str = "icustay_id"
    PROC_TIME_COL: str = "starttime"
    PROC_ITEMID_COL: str = "itemid"
    PROC_LABEL_COL: str = "label"

    HEART_RATE_ITEMS: list = [211, 220045]
    RESP_RATE_ITEMS: list = [618, 615, 220210, 224690]
    SPO2_ITEMS: list = [646, 220277]
    TEMPERATURE_ITEMS: list = [676, 223761, 678, 223762]
    SBP_ITEMS: list = [51, 442, 455, 6701, 220179, 220050]
    DBP_ITEMS: list = [8368, 8440, 8441, 8555, 220180, 220051]
    MAP_ITEMS: list = [52, 456, 6702, 443, 220052, 220181, 225312]
    GCS_ITEMS: list = [198, 220739]

    WBC_ITEMS: list = [51300, 51301]
    CREATININE_ITEMS: list = [50912]
    LACTATE_ITEMS: list = [50813]
    HEMOGLOBIN_ITEMS: list = [51222]
    PLATELETS_ITEMS: list = [51265]
    SODIUM_ITEMS: list = [50983]
    POTASSIUM_ITEMS: list = [50971]
    BILIRUBIN_ITEMS: list = [50885]

    HEART_RATE_LOW: float = 60.0
    HEART_RATE_HIGH: float = 100.0
    RESP_RATE_LOW: float = 12.0
    RESP_RATE_HIGH: float = 20.0
    SPO2_LOW: float = 95.0
    TEMP_LOW: float = 36.0
    TEMP_HIGH: float = 38.0
    WBC_LOW: float = 4.0
    WBC_HIGH: float = 11.0
    CREATININE_HIGH: float = 1.2
    LACTATE_HIGH: float = 2.0
    HEMOGLOBIN_LOW: float = 7.0
    PLATELETS_LOW: float = 150.0

    class Config:
        env_file = ".env"

settings = Settings()
