# Task 8 — The End-to-End Pipeline
**PlaceMux AI/ML Developer · Phase 1 Industry Immersion**

## ONE COMMAND
```bash
python run_pipeline.py
```
Automatically: Load → Validate → Feature Engineer → Split → Train (sklearn Pipeline) → Evaluate → Save Model + Metrics + Log

## Pipeline Results
| Split | F1 | Accuracy | ROC-AUC |
|---|---|---|---|
| Validation | 0.7869 | 0.7933 | 0.8488 |
| Test | 0.6961 | 0.7067 | 0.7917 |

## Commands
```bash
python run_pipeline.py                    # default (random_forest)
python run_pipeline.py --model logistic   # swap model — zero code changes
python run_pipeline.py --predict          # live demo + edge cases
python run_pipeline.py --verify-repro     # run twice, confirm identical metrics
```

## Pipeline Architecture
```
data/loan_applicants.csv
         ↓
[1] Load & validate schema (clear errors, not tracebacks)
         ↓
[2] Feature engineering (8 domain-derived features from Task 7)
         ↓
[3] 70/15/15 stratified split
         ↓
[4] sklearn Pipeline:  ColumnTransformer (Impute+Scale+Encode) → Model
    Preprocessing travels WITH the model (pipeline integrity ✅)
         ↓
[5] Evaluation gate: accuracy, precision, recall, F1, ROC-AUC
         ↓
[6] Artifacts: model.joblib + metrics.json + experiment_log.csv
```

## Artifacts Produced
| File | Contents |
|---|---|
| `artifacts/model.joblib` | Entire sklearn Pipeline (preprocessor + model) |
| `artifacts/metrics.json` | Val + test metrics |
| `artifacts/experiment_log.csv` | Every run's parameters and results |

## Edge Cases Handled
- Missing dataset file → clear error message
- Empty dataset → clear error message
- Missing required columns → lists exactly which columns are missing
- Null feature values → median/mode imputed inside pipeline
- Schema drift → validation gate catches it before training

## Evaluation Checklist
- [x] One command runs the complete pipeline
- [x] Preprocessing inside sklearn Pipeline (not outside)
- [x] Preprocessing travels with model (model.joblib = full pipeline)
- [x] Fixed seed=42 — identical results every run
- [x] Evaluation gate: reports metrics, not just "model trained"
- [x] Artifacts: model.joblib + metrics.json + experiment_log.csv
- [x] Live demo with 3 applicant types + 2 error cases
- [x] Reproducibility: run twice → same numbers
