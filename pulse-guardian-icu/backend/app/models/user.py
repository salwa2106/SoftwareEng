from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default="clinician")  # admin, clinician
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, unique=True, index=True)
    gender = Column(String)
    age = Column(Float)
    dob = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admissions = relationship("Admission", back_populates="patient")

class Admission(Base):
    __tablename__ = "admissions"
    id = Column(Integer, primary_key=True, index=True)
    hadm_id = Column(Integer, unique=True, index=True)
    subject_id = Column(Integer, ForeignKey("patients.subject_id"))
    admission_type = Column(String)
    admittime = Column(String)
    dischtime = Column(String)
    hospital_los = Column(Float)  # length of stay in days
    diagnosis = Column(Text)
    insurance = Column(String)
    marital_status = Column(String)
    ethnicity = Column(String)

    patient = relationship("Patient", back_populates="admissions")
    icustays = relationship("ICUStay", back_populates="admission")
    risk_scores = relationship("RiskScore", back_populates="admission")
    alerts = relationship("Alert", back_populates="admission")
    reports = relationship("Report", back_populates="admission")

class ICUStay(Base):
    __tablename__ = "icustays"
    id = Column(Integer, primary_key=True, index=True)
    icustay_id = Column(Integer, unique=True, index=True)
    hadm_id = Column(Integer, ForeignKey("admissions.hadm_id"))
    subject_id = Column(Integer, index=True)
    first_careunit = Column(String)
    last_careunit = Column(String)
    intime = Column(String)
    outtime = Column(String)
    los = Column(Float)  # ICU length of stay in days

    # Vital signs (aggregated)
    heart_rate_mean = Column(Float)
    heart_rate_min = Column(Float)
    heart_rate_max = Column(Float)
    resp_rate_mean = Column(Float)
    resp_rate_min = Column(Float)
    resp_rate_max = Column(Float)
    spo2_mean = Column(Float)
    spo2_min = Column(Float)
    spo2_max = Column(Float)
    bp_systolic_mean = Column(Float)
    bp_systolic_min = Column(Float)
    bp_systolic_max = Column(Float)
    bp_diastolic_mean = Column(Float)
    bp_diastolic_min = Column(Float)
    bp_diastolic_max = Column(Float)

    # Lab results (aggregated)
    creatinine_mean = Column(Float)
    creatinine_max = Column(Float)
    glucose_mean = Column(Float)
    glucose_max = Column(Float)
    hemoglobin_mean = Column(Float)
    hemoglobin_min = Column(Float)
    potassium_mean = Column(Float)
    sodium_mean = Column(Float)
    wbc_mean = Column(Float)
    wbc_max = Column(Float)

    admission = relationship("Admission", back_populates="icustays")

class RiskScore(Base):
    __tablename__ = "risk_scores"
    id = Column(Integer, primary_key=True, index=True)
    hadm_id = Column(Integer, ForeignKey("admissions.hadm_id"))
    icustay_id = Column(Integer, index=True)
    score = Column(Float)
    risk_level = Column(String)  # Low, Medium, High
    contributing_factors = Column(Text)  # JSON string
    calculated_at = Column(DateTime(timezone=True), server_default=func.now())

    admission = relationship("Admission", back_populates="risk_scores")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    hadm_id = Column(Integer, ForeignKey("admissions.hadm_id"))
    icustay_id = Column(Integer, index=True)
    alert_type = Column(String)   # deterioration, vitals, lab
    severity = Column(String)     # warning, critical
    message = Column(Text)
    indicator = Column(String)
    value = Column(Float)
    threshold = Column(Float)
    is_acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admission = relationship("Admission", back_populates="alerts")

class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    hadm_id = Column(Integer, ForeignKey("admissions.hadm_id"))
    generated_by = Column(Integer, ForeignKey("users.id"))
    content = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    admission = relationship("Admission", back_populates="reports")
