# Task 3 — Core Architecture
**PlaceMux AI/ML Developer · Phase 1 Industry Immersion**

## What this is
A modular, config-driven train/evaluation skeleton for binary classification (credit card fraud detection). Any sklearn-compatible model plugs in without rewriting data loading, preprocessing, or evaluation logic.

## Architecture
```
config/config.yaml
        │
        ▼
    train.py  (single harness)
        │
   ┌────┴────┐
   ▼         ▼
src/data  src/models
loader.py  model.py (factory)
   │         │
   └────┬────┘
        ▼
src/features/preprocessing.py  (sklearn Pipeline)
        │
        ▼
src/evaluation/evaluate.py
        │
        ▼
experiments/metrics.csv
```

## Quick Start
```bash
pip install -r requirements.txt

# Run with default model (dummy baseline)
python train.py

# Swap model — no code changes needed
python train.py --model logistic
python train.py --model random_forest
```

## How to Add a New Model (3 steps)
1. **Register** — Add to `REGISTRY` in `src/models/model.py`:
   ```python
   from sklearn.svm import SVC
   REGISTRY["svm"] = SVC
   ```
2. **Configure** — Update `config/config.yaml`:
   ```yaml
   model:
     name: "svm"
     params:
       kernel: "rbf"
   ```
3. **Run** — `python train.py` — data, preprocessing, eval, logging all reuse unchanged.

## Project Structure
```
Task3_Core_Architecture/
├── config/config.yaml        ← all paths, params, seeds
├── data/credit_fraud_dataset.csv
├── experiments/metrics.csv   ← auto-generated experiment log
├── notebooks/demo.ipynb
├── src/
│   ├── data/loader.py        ← load + split
│   ├── features/preprocessing.py  ← sklearn ColumnTransformer
│   ├── models/model.py       ← model factory / registry
│   ├── evaluation/evaluate.py ← all metric logic
│   └── pipeline.py           ← assembles preprocessor + model
├── train.py                  ← single entry point
└── requirements.txt
```

## Evaluation Checklist
- [x] Modular package structure (data / features / models / evaluation)
- [x] YAML config controls dataset path, model, params, seed, split sizes
- [x] sklearn Pipeline (ColumnTransformer + estimator)
- [x] Single train/eval harness — `python train.py`
- [x] Baseline (DummyClassifier) wired through architecture
- [x] Model swap proven: dummy → logistic → random_forest, zero rewrites
- [x] Metrics auto-logged to `experiments/metrics.csv`
- [x] Real dataset (1500 rows, 13 features)
- [x] New model addition documented above
