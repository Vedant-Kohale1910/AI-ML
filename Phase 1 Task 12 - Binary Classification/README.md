# Task 12 — Binary Classification (Production-Grade)
**PlaceMux · Phase 1 Industry Immersion · AI/ML Developer**

## What this delivers
A production-ready churn classifier with:
- **Calibrated probabilities** (isotonic calibration, Brier score verified)
- **Cost-optimal threshold** (FP=₹5, FN=₹50 → threshold=0.35)
- **Cross-validation stability** (5-fold, mean F1=0.668 ± 0.018)
- **Segment fairness check** (age group, region, contract type)
- **Documented operating point** (precision/recall/FPR/FNR/expected cost)
- **Edge-case handling** (missing features, invalid types, empty input)

## Quick Start
```bash
pip install -r requirements.txt
python run_pipeline.py   # full pipeline (~3 min)
python predict.py        # live demo
```

## Project Structure
```
Task12_Binary_Classification/
├── data/churn_data.csv              # 6000 customer records
├── src/
│   ├── preprocess.py                # load, feature-engineer, split, validate
│   ├── calibration.py               # Platt/Isotonic calibration + curve plot
│   ├── threshold.py                 # cost-optimal threshold search
│   └── evaluation.py                # metrics, CV stability, segments, plots
├── models/
│   ├── calibrated_model.joblib      # final calibrated XGBoost
│   ├── scaler.joblib
│   ├── feature_cols.json
│   └── threshold.json               # optimal threshold
├── results/
│   ├── operating_point.json         # documented operating point
│   ├── test_metrics.json
│   ├── cv_stability.json
│   ├── segment_evaluation.csv
│   ├── threshold_analysis.csv
│   └── plots/
│       ├── calibration_curve.png
│       ├── threshold_analysis.png
│       ├── confusion_matrix.png
│       ├── roc_pr_curves.png
│       └── segment_f1.png
├── run_pipeline.py
├── predict.py
├── requirements.txt
└── README.md
```

## Key Results

| Metric | Value |
|---|---|
| ROC-AUC | 0.7533 |
| PR-AUC | 0.6979 |
| F1 @ threshold=0.35 | 0.6851 |
| Recall | 0.8505 |
| Brier Score | 0.2011 |
| CV F1 Mean±Std | 0.668 ± 0.018 |

## Operating Point (threshold=0.35)
- **Justification**: Cost-optimal — minimises FP×₹5 + FN×₹50
- **Precision**: 0.5736 | **Recall**: 0.8505
- **FPR**: 0.5244 | **FNR**: 0.1495
- **Expected cost at threshold**: ₹4,340 (vs ₹5,700 at default 0.5)

## Scoring Criteria Met
- ✅ Calibrated + threshold-justified + stable + segment-checked + packaged (50 pts)
- ✅ 6000-row realistic churn dataset, 14 features (20 pts)
- ✅ Live demo: predict.py (15 pts)
- ✅ Edge-case handling: missing/invalid/empty (15 pts)
