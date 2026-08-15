# Task 4 — The Pre-Processing Protocol
**PlaceMux AI/ML Developer · Phase 1 Industry Immersion**

## What this delivers
A **fitted, leak-free preprocessing pipeline** reusable at both train time and inference time.

## Preprocessing Protocol

| Feature Type | Step 1 | Step 2 |
|---|---|---|
| Numeric (12 cols) | Median Imputation | StandardScaler |
| Categorical (1 col) | MostFrequent Imputation | OneHotEncoder (handle_unknown='ignore') |

**ColumnTransformer** applies both pipelines in parallel. **Fitted only on X_train.**

## Quick Start
```bash
pip install -r requirements.txt

# Full train + preprocessing
python train.py

# Inference demo — load saved preprocessor, transform new rows
python train.py --demo-inference
```

## The Leak-Free Rule (critical)
```python
# ✅ CORRECT
preprocessor.fit_transform(X_train)   # learn params from train only
preprocessor.transform(X_val)         # apply same params — no re-fitting
preprocessor.transform(X_test)        # apply same params — no re-fitting

# ❌ WRONG (leakage)
preprocessor.fit_transform(X_test)    # would contaminate params with test info
```

## Artifact Reuse at Inference
```python
import joblib
preprocessor = joblib.load("artifacts/preprocessor.pkl")
X_new_processed = preprocessor.transform(new_data)  # same params, no re-fitting
```

## Project Structure
```
Task4_Preprocessing/
├── config/config.yaml              ← all settings
├── data/credit_fraud_dataset.csv   ← 1500 rows, 195 missing cells
├── artifacts/preprocessor.pkl      ← saved fitted preprocessor
├── experiments/metrics.csv         ← auto-logged results
├── notebooks/preprocessing_demo.ipynb
├── src/
│   ├── data/loader.py
│   ├── features/preprocessing.py  ← TASK 4 core
│   ├── models/model.py
│   └── evaluation/evaluate.py
└── train.py
```

## Evaluation Checklist
- [x] Transforms listed per feature type (numeric + categorical)
- [x] Pipeline fitted only on training data — no leakage
- [x] Median imputation for numeric missing values
- [x] MostFrequent imputation for categorical missing values
- [x] StandardScaler for numeric features
- [x] OneHotEncoder for categorical (handle_unknown='ignore')
- [x] ColumnTransformer combines both pipelines
- [x] transform() used on val/test — never fit_transform()
- [x] Leakage verified and printed
- [x] preprocessor.pkl saved for inference reuse
- [x] Inference demo with unseen category + missing values works
- [x] Real dataset with 195 genuine missing cells
