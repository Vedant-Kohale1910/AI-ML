# Task 17 — Public API, Webhooks & ATS Partner Integrations
PlaceMux · Phase 3 · Sprint D

## Run (demo/reports — no server needed)
```bash
pip install fastapi uvicorn numpy pandas scikit-learn pydantic
python run_pipeline.py   # generates all reports
python demo.py           # 2-min live demo
```

## Run live API server
```bash
uvicorn src.api.app:app --reload
# Open http://127.0.0.1:8000/docs for partner documentation
```

## API keys for testing
| Key | Tier | Limit |
|---|---|---|
| partner-key-free | free | 100/day, 10/min |
| partner-key-standard | partner | 5,000/day, 100/min |
| partner-key-enterprise | enterprise | unlimited |

## Endpoints
| Endpoint | Purpose |
|---|---|
| POST /v2/score | Score one candidate vs one job |
| POST /v2/match | Top-K candidates for a job (ATS) |
| POST /v1/score | Deprecated (sunset 2026-06-30) |
| GET  /v2/health | Health check |
| GET  /docs | OpenAPI documentation |
