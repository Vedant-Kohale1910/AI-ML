# PlaceMux — Task 06: AI/ML Quality Baseline

**Phase 2 · Week 3 · Industry Immersion**  
**Role:** AI/ML Engineer  
**Focus:** Baseline match quality before monetization changes behavior

---

## What this does

This module builds and evaluates a job-candidate matching baseline for PlaceMux. Given a student's verified skill scores and a job description's required skills, it ranks and scores how well they match — with a plain-English explanation for every decision.

The goal isn't a fancy model. It's a defensible, explainable, measurable baseline that the team can monitor, compare against, and improve over time.

---

## Folder structure

```
placemux_task06/
├── data/
│   ├── raw/               # Synthetic student + job data as generated
│   └── processed/         # Cleaned, feature-engineered splits
├── experiments/           # MLflow runs (auto-created on first run)
├── notebooks/             # Exploration notebook
├── reports/               # Metrics, confusion matrices, PR curves
├── src/
│   ├── api/               # FastAPI inference endpoint
│   ├── features/          # Feature engineering pipeline
│   ├── models/            # Baseline + ranker training/evaluation
│   └── utils/             # Data generation, logging helpers
├── tests/                 # Unit tests
├── requirements.txt
└── README.md
```

---

## Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic data
python src/utils/data_generator.py

# 3. Build features and run baseline
python src/features/feature_engineering.py
python src/models/baseline.py

# 4. Train the ranker and evaluate
python src/models/ranker.py

# 5. Start the inference API
uvicorn src.api.app:app --reload --port 8000

# 6. Run tests
pytest tests/ -v
```

---

## Metrics (baseline run)

Metrics are saved to `reports/metrics.json` after each run and logged to MLflow.

Key numbers to look at:
- **Precision@K** — of the top-K matches shown, how many are actually relevant
- **Recall@K** — of all relevant jobs, how many did we surface in top-K
- **False Positive Rate** — how often we show a bad match
- **NDCG** — ranking quality (does the best match come first?)

---

## Explainability

Every match output includes a `reasons` field — e.g.:

```json
{
  "job_id": "JD_042",
  "score": 0.81,
  "reasons": [
    "Student has 87% skill overlap with required skills",
    "Verified Python score (92) exceeds job threshold (70)",
    "Missing: Docker (required, not verified)"
  ]
}
```

---

## Definition of done (from study guide)

- [x] Match-quality baseline recorded  
- [x] "Quality baseline" complete, persisted, demoable end-to-end  
- [x] Real (synthetic, real-shaped) sample data used — not a toy example  
- [x] Numbers reported — not just "it works"

---

## Self-check

- Can you show Quality baseline working live? → `python src/models/baseline.py`
- Walk through one real example? → `python src/models/ranker.py --demo`
- Numbers on real sample data? → `reports/metrics.json`
