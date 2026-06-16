# ICU Risk Prediction System

Academic demonstration of a full-stack ICU patient risk monitoring system built on MIMIC-III data structure.

> **FOR ACADEMIC/DEMONSTRATION USE ONLY. NOT FOR CLINICAL USE.**

## Architecture

- **Backend**: FastAPI + Python (pandas, numpy)
- **Frontend**: Next.js 14 (App Router) + Tailwind CSS + Recharts
- **Data**: MIMIC-III compatible CSV structure (sample data included)

## Quick Start

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Visit http://localhost:8000/docs for API documentation.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

## Using Real MIMIC-III Data

Place MIMIC-III CSV files in `backend/data/`:
- patients.csv
- admissions.csv
- icustays.csv
- chartevents.csv (large - may need chunked loading)
- labevents.csv
- prescriptions.csv
- procedures.csv
- d_labitems.csv
- d_items.csv

Sample synthetic data is provided in `backend/data/sample/` for demonstration.

## Risk Scoring

Rule-based scoring using vital sign and lab thresholds:
- **Low**: 0-1 abnormal values
- **Medium**: 2-3 abnormal values
- **High**: 4+ abnormal values or critical single values

This is NOT a validated clinical decision support tool.
