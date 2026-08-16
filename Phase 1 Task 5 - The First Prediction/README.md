# Task 5 — The First Prediction
**PlaceMux AI/ML Developer · Phase 1 Industry Immersion**

## What this delivers
First real predictive model with validation metrics shown against an explicit baseline, plus error analysis and experiment log.

## Results Summary

| Model | Val F1 | Val Acc | Lift vs Baseline |
|---|---|---|---|
| Majority-Class Baseline | 0.4156 | 71.1% | — |
| **Logistic Regression** | **0.7147** | **78.7%** | **+0.2991 F1** |
| Decision Tree | 0.6583 | 72.4% | +0.2427 F1 |

## Quick Start
```bash
pip install -r requirements.txt

# Run single model
python run.py --model logistic

# Compare two models head-to-head
python run.py --model logistic --model2 decision_tree
```

## Evaluation Checklist
- [x] Baseline computed first (majority class → F1=0.42)
- [x] First model trained (Logistic Regression) through harness
- [x] Validation metrics on unseen data (NOT training accuracy)
- [x] Explicit baseline comparison with lift calculation
- [x] Error analysis — false negatives and false positives inspected for patterns
- [x] Experiment log auto-updated with all run details
- [x] Final test set evaluated once (unbiased)
- [x] Next improvement identified from error evidence

## Error Patterns Found
- **33 false negatives** (missed fraud): lower dispute history — harder borderline cases
- **15 false positives** (false alarm): higher transaction amounts trigger suspicion incorrectly
- **Next step:** `class_weight='balanced'` to improve fraud recall

## Project Structure
```
Task5_First_Prediction/
├── data/credit_fraud_dataset.csv
├── src/
│   ├── preprocessing.py    ← leak-free pipeline (Task 4 protocol)
│   ├── baseline.py         ← majority class baseline
│   ├── train.py            ← model factory (logistic, decision_tree)
│   └── evaluate.py         ← metrics + error analysis + experiment logging
├── results/
│   ├── baseline_vs_model.png
│   ├── confusion_matrices.png
│   └── error_analysis_logistic.csv
├── experiment_log/
│   └── experiment_log.csv
├── notebooks/Task_5_First_Prediction.ipynb
└── run.py                  ← single harness entry point
```
