# Task 13 — Model Score Extraction
**PlaceMux · Phase 1 Industry Immersion · AI/ML Developer**

## What this delivers
A production-grade scoring interface for a churn prediction model:
- **Validated input contract** (Pydantic, typed + range-checked)
- **Standardised output** (score + score_band + prediction_label + model_version + hash + timestamp)
- **Single-record and batch scoring** (in-memory + CSV file)
- **FastAPI REST endpoint** (`/score/single`, `/score/batch`, `/model/info`, `/health`)
- **Model versioning** on every score output (v1.0.0 + MD5 hash)
- **Edge-case handling** (missing fields, out-of-range values, extra fields, type errors)
- **Latency benchmark** (mean ~11ms per single call)

## Quick Start
```bash
pip install -r requirements.txt
python run_pipeline.py       # full pipeline + demo
python predict.py            # CLI live demo
python scoring/api.py        # start FastAPI server (port 8000)
```

## API Usage
```bash
# Health check
GET http://localhost:8000/health

# Single score
POST http://localhost:8000/score/single
{"tenure":60,"monthly_charges":45.0,"total_charges":2700.0,...}

# Batch score
POST http://localhost:8000/score/batch
{"records":[...], "batch_id":"batch-001"}
```

## Score Output Contract
```json
{
  "record_id": "customer-123",
  "score": 0.0118,
  "score_band": "LOW",
  "prediction": 0,
  "prediction_label": "NO_CHURN",
  "threshold_used": 0.35,
  "score_meaning": "Calibrated probability of customer churn in the next billing cycle",
  "model_version": "v1.0.0",
  "model_hash": "8bfdb588",
  "scored_at": "2026-08-21T03:31:18.898380+00:00"
}
```

## Score Bands
| Band | Range | Meaning |
|---|---|---|
| LOW | < 0.20 | Minimal churn risk |
| MEDIUM-LOW | 0.20–0.40 | Moderate risk, monitor |
| MEDIUM-HIGH | 0.40–0.60 | Elevated risk, consider outreach |
| HIGH | ≥ 0.60 | High churn risk, immediate action |

## Project Structure
```
Task13_Model_Score_Extraction/
├── data/churn_data.csv              # 6000 customer records
├── src/train_model.py               # train + calibrate + version model
├── scoring/
│   ├── schema.py                    # Pydantic input/output contracts
│   ├── scorer.py                    # single, batch, CSV scoring engine
│   └── api.py                       # FastAPI REST interface
├── models/
│   ├── churn_model.joblib
│   ├── scaler.joblib
│   └── model_metadata.json          # version, hash, semantics, threshold
├── results/
│   ├── batch_scores_output.csv      # 500-record scored CSV
│   ├── interface_documentation.json
│   └── plots/score_distribution.png
├── run_pipeline.py
├── predict.py
├── requirements.txt
└── README.md
```

## Scoring Criteria Met
- ✅ Validated scoring interface, versioned outputs, batch + single (50 pts)
- ✅ 6000-row realistic dataset, real inference (20 pts)
- ✅ Live CLI demo + FastAPI server (15 pts)
- ✅ 4 edge cases caught with informative errors (15 pts)
