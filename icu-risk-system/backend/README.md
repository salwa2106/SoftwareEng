# ICU Risk Prediction - Backend

FastAPI backend serving patient risk data from MIMIC-III compatible CSV files.

## Setup

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

- `GET /api/health` - System health check
- `GET /api/patients` - List patients (paginated)
- `GET /api/patients/{id}` - Patient details
- `GET /api/patients/{id}/timeline` - Hourly timeline with risk scores
- `GET /api/patients/{id}/risk` - Current risk assessment
- `GET /api/patients/{id}/alerts` - Clinical alerts

## Configuration

Edit `app/config.py` or use `.env` file to configure:
- Column name mappings (if your CSVs differ from MIMIC-III schema)
- Item IDs for vital signs and labs
- Risk thresholds
