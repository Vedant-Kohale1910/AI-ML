# Task 14 — Fairness, Bias Audit & Explainability
PlaceMux · Phase 3 · Sprint C

## Run
```bash
pip install numpy pandas scikit-learn
python run_pipeline.py   # audit + mitigation + explanations → reports/
python demo.py           # 2-min live demo
```

## What was built
| File | Purpose |
|---|---|
| src/fairness/audit.py | Demographic Parity + Equal Opportunity audit across groups |
| src/fairness/mitigation.py | Post-processing score calibration |
| src/explainability/explanation_engine.py | Feature-attribution → plain-English API response |
| run_pipeline.py | End-to-end pipeline → reports/ |
| demo.py | Live 2-min demo |

## Key results
| Group | DPD Before | DPD After | Target |
|---|---|---|---|
| experience_tier | 0.25 | 0.09 | <0.10 ✓ |

## Design decisions
- Post-processing mitigation chosen (model-agnostic, auditable, reversible)
- Equal Opportunity chosen over demographic parity (conditions on merit)
- Feature-attribution explanations chosen over SHAP/LIME (interpretable, deterministic)
