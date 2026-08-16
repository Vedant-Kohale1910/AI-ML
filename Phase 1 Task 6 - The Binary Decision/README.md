# Task 6 — The Binary Decision
**PlaceMux AI/ML Phase 1** | Binary classifier with confusion matrix, precision/recall, ROC/PR curves, justified threshold, live demo.

## Results (Test Set, threshold=0.35)
| Model | F1 | ROC-AUC | Recall | Precision |
|---|---|---|---|---|
| Baseline | 0.000 | — | 0% | — |
| Logistic Regression | ~0.63 | ~0.83 | — | — |
| **Random Forest (BEST)** | **0.65** | **0.84** | **0.64** | **0.66** |

**Justified Threshold = 0.35** — FN (missed fraud) costs more than FP (false alarm). Lower threshold maximises recall.

## Quick Start
```bash
pip install -r requirements.txt
python run.py           # full train + evaluation
python run.py --predict # live prediction + edge cases
```

## Evaluation Checklist
- [x] Confusion matrix (TP/FP/TN/FN)
- [x] Precision, Recall, F1, Accuracy, ROC-AUC, PR-AUC
- [x] ROC + PR curves for both models
- [x] Class imbalance analysis (73/27, ratio 2.7:1)
- [x] Threshold analysis 0.10–0.90 with business cost reasoning
- [x] Threshold=0.35 justified; tuned on val, evaluated once on test
- [x] Live prediction demo (6 test cases)
- [x] Edge cases: missing value, unseen category, invalid type, out-of-range
