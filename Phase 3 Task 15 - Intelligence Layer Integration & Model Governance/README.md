# Task 15 — Intelligence Layer Integration & Model Governance
PlaceMux · Phase 3 · Sprint C

## Run
```bash
pip install numpy pandas scikit-learn
python run_pipeline.py   # registers models, detects drift, rollback, model card
python demo.py           # 2-min live demo
```

## What was built
| File | Purpose |
|---|---|
| src/governance/model_registry.py | JSON-backed registry: versions, metrics, lineage, status |
| src/governance/drift_detection.py | PSI data drift + nDCG performance drift with retraining trigger |
| src/governance/model_card.py | Google Model Card standard generator |
| run_pipeline.py | Full governance pipeline |
| demo.py | Live 2-min demo |

## Reports generated
- model_registry.json / model_registry.csv — full version history
- drift_report.md — PSI + weekly performance drift (trigger at week 5)
- retraining_log.csv — weekly snapshots
- rollback_report.md — rollback event record
- model_card.md — governance document for production model
