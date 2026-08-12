# Pulse Guardian ICU
### AI-Powered ICU Clinical Decision Support System
**Based on MIMIC-III Clinical Database · Software Engineering Final Project**

> ⚠️ **FOR ACADEMIC / DEMO USE ONLY** — This system is not approved for real clinical decisions.

---

## Overview

Pulse Guardian ICU is a full-stack AI-based clinical decision support system that processes ICU patient data from the MIMIC-III database and provides an interactive dashboard with:

- 🔴 **Dynamic risk scoring** (0–100) with Low / Medium / High classification
- 🚨 **Early deterioration detection** and real-time alerts
- 📊 **Vital signs and lab result charts** with normal range references
- 🧠 **Explainability** — which indicators contributed to the risk score
- 📅 **Clinical timeline** per patient
- 📋 **Medical report generation**
- 🔍 **Search and filtering** by patient ID, risk level, gender, admission type
- 📈 **Model evaluation metrics** (Accuracy, Precision, Recall, F1-Score, AUC-ROC)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18 + React Router + Recharts |
| Backend | Python 3.10+ · FastAPI · SQLAlchemy |
| Database | SQLite (development) |
| Risk Engine | Rule-based + sklearn-ready |
| Styling | Custom CSS design system (dark clinical theme) |

---

## Project Structure

```
pulse-guardian-icu/
├── backend/
│   ├── app/
│   │   ├── api/          ← REST API routes
│   │   ├── core/         ← DB, security, config
│   │   ├── ml/           ← Risk prediction engine
│   │   ├── models/       ← SQLAlchemy models
│   │   ├── services/     ← Data loader
│   │   └── main.py       ← FastAPI app entry point
│   ├── data/             ← Place your CSV here
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/   ← Reusable UI components
│   │   ├── hooks/        ← Auth context
│   │   ├── pages/        ← All page components
│   │   ├── utils/        ← Axios API client
│   │   ├── App.js
│   │   └── index.css     ← Design system
│   └── package.json
└── README.md
```

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- npm or yarn

---

### Backend Setup

```bash
# 1. Navigate to backend
cd pulse-guardian-icu/backend

# 2. Create virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy environment file
cp .env.example .env

# 5. Run the backend
uvicorn app.main:app --reload --port 8000
```

The backend will automatically:
- Create the SQLite database (`pulse_guardian.db`)
- Create a default admin user (`admin` / `admin123`)
- Generate 200 synthetic demo patients if no data exists

**API Documentation:** http://localhost:8000/api/docs

---

### Frontend Setup

```bash
# 1. Navigate to frontend (new terminal)
cd pulse-guardian-icu/frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm start
```

The frontend runs at: http://localhost:3000

---

### Default Login
```
Username: admin
Password: admin123
```

---

## Connecting Real MIMIC-III Data

If you have the cleaned MIMIC-III CSV:

1. Log in as admin
2. Navigate to **Data Import** (sidebar)
3. Upload your CSV file
4. The system auto-detects column names (see `backend/app/services/data_loader.py` for supported column name variants)

**Expected CSV columns** (any naming variant works):
- `subject_id`, `hadm_id`, `icustay_id`
- `gender`, `age`, `admission_type`, `diagnosis`
- `heart_rate_mean/min/max`, `resp_rate_mean/min/max`
- `spo2_mean/min/max`, `bp_systolic_mean/min/max`
- `creatinine_mean/max`, `glucose_mean/max`
- `hemoglobin_mean/min`, `potassium_mean`, `sodium_mean`
- `wbc_mean/max`, `los` (ICU length of stay), `hospital_los`

---

## Risk Scoring System

| Score | Level | Description |
|---|---|---|
| 0–39 | 🟢 Low | Stable, monitoring recommended |
| 40–69 | 🟡 Medium | Elevated risk, close monitoring required |
| 70–100 | 🔴 High | Critical, immediate clinical attention |

**Indicators contributing to risk:**
Heart Rate, Respiratory Rate, SpO₂, Blood Pressure (systolic + diastolic),
Creatinine, Glucose, Hemoglobin, Potassium, Sodium, WBC, ICU Length of Stay

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | Login |
| GET | `/api/patients/` | List patients (with filters) |
| GET | `/api/patients/stats` | Dashboard statistics |
| GET | `/api/patients/{id}` | Patient details |
| GET | `/api/patients/{id}/timeline` | Clinical timeline |
| GET | `/api/risk/{hadm_id}` | Risk score |
| GET | `/api/risk/metrics` | Model evaluation metrics |
| GET | `/api/alerts/` | Active alerts |
| POST | `/api/reports/{hadm_id}/generate` | Generate report |
| POST | `/api/data/import` | Upload CSV |
| POST | `/api/data/generate-demo` | Generate demo data |

---

## Demo Flow (For Presentation)

1. Open http://localhost:3000
2. Login with `admin` / `admin123`
3. **Dashboard** — view risk distribution and critical alerts
4. **Patient List** — filter by High Risk, browse table
5. Click a high-risk patient → **Patient Detail**
6. Explore tabs: Overview → Vitals → Labs → Risk → Timeline → Alerts
7. Click **Generate Report** to produce a clinical summary
8. Navigate to **Alerts** page — acknowledge an alert
9. Navigate to **Model Metrics** — show Accuracy, F1, AUC-ROC

---

## Team

- Layan Shawahny
- Dana Naser
- George Khalil
- Salwa

---

*Pulse Guardian ICU · Software Engineering Final Project · MIMIC-III Dataset · Academic Use Only*
