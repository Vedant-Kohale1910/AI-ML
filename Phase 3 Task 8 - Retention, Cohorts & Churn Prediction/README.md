# Task 8 — Retention, Cohorts & Churn Prediction
## PlaceMux · Phase 3 · Sprint B

**The bar:** Model finds at-risk users early enough that an intervention is still possible.

## Quick Start
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python demo.py
```

## Results
| Metric | Baseline (14-day rule) | Churn Model |
|---|---|---|
| ROC-AUC | 0.9874 | 0.9937 |
| Precision | — | 0.9875 |
| Recall | — | 1.0000 |
| Lift | — | +0.0063 |

## Design Decisions
- **Churn label**: ≥30 days no login AND no application
- **Horizon**: Predict 14 days before window closes (Growth team lead time)
- **Model**: Logistic Regression on RFM features — interpretable, no label leak
- **Rejected**: Survival analysis (overkill); raw RFM rule only (model wins)

## Demo Sections
| Section | Content |
|---|---|
| A | Churn definition + horizon + label-leak check |
| B | Evaluation vs baseline (AUC, P, R, lift) |
| C | Worked example with plain-English explanation |
| D | Prioritized at-risk list → Growth team |
| E | Model failure → rule-based fallback |
| F | Fairness check across cohorts |

## Hand-off
- `reports/at_risk_candidates.csv` → Growth / Data-Analyst
- Intervention: HIGH risk → email+rec; MEDIUM → push; LOW → monitor
- Re-train trigger: weekly or AUC drop > 0.05
