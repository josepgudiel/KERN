# Analytic — FastAPI Backend

## Setup

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# add your GROQ_API_KEY to .env
uvicorn main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload CSV/Excel file |
| GET | `/action-center?session_id=` | Ranked recommendations |
| GET | `/whats-selling?session_id=` | Clusters + basket rules |
| GET | `/when-to-staff?session_id=` | Day-of-week patterns |
| GET | `/forecast?session_id=&weeks=8` | Revenue forecast |
| GET | `/anomalies?session_id=` | Anomaly detection |
| POST | `/advisor` | AI chat advisor |
