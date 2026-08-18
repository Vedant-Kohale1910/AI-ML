# Task 9 — Hyperparameter Tuning
**PlaceMux AI/ML Developer · Phase 1 Industry Immersion**

## ONE COMMAND
```bash
python run_tuning.py
```

## Results — Baseline vs Tuned (Test Set)

| Metric | Task 8 Baseline | Task 9 Tuned | Gain |
|---|---|---|---|
| F1-Macro | 0.6961 | **0.7257** | **+0.0296** |
| Accuracy | 0.7067 | 0.7333 | +0.0266 |
| ROC-AUC | 0.7917 | 0.8001 | +0.0084 |

**Improvement confirmed on held-out test set ✅**

## Best Configuration Found
```
n_estimators    : 300
max_depth       : 15
min_samples_split: 5
min_samples_leaf : 4
max_features    : log2
```
Found via: **RandomizedSearchCV | 30 iterations | 5-fold CV | scoring=f1_macro**

## Commands
```bash
python run_tuning.py               # full tuning pipeline
python run_tuning.py --predict     # live demo with tuned model
python run_tuning.py --show-results # display saved comparison
```

## Pipeline (what happens in one command)
```
[1] Load + validate schema
[2] Feature engineering (Task 7 domain features)
[3] 70/15/15 split (identical to Task 8 for fair comparison)
[4] Record Task 8 baseline (test set — one evaluation)
[5] RandomizedSearchCV on TRAIN only — test set NEVER touched
[6] Evaluate tuned model on val then test (ONE test evaluation)
[7] Compare baseline vs tuned — print improvement table
[8] Save: tuned_model.joblib + tuning_results.json + cv_results.csv + comparison.csv
```

## Artifacts
| File | Contents |
|---|---|
| `artifacts/tuned_model.joblib` | Full sklearn Pipeline (preprocessor + tuned RF) |
| `artifacts/tuning_results.json` | Best params, CV score, baseline vs tuned F1 |
| `artifacts/cv_results.csv` | All 30 candidate configurations ranked by CV F1 |
| `artifacts/tuning_comparison.csv` | Baseline vs tuned comparison table |

## Key Rules Followed
- ✅ Test set NOT touched during hyperparameter search
- ✅ CV used to select best config (not val set directly)
- ✅ Only meaningful parameters tuned (n_estimators, max_depth, min_samples_split, min_samples_leaf, max_features)
- ✅ Gain confirmed on held-out test set after tuning
- ✅ Reproducible (seed=42 everywhere)
