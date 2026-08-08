# Task 24 — Disaster Recovery, Chaos Testing & Business Continuity
PlaceMux · Phase 3 · Sprint E

## Run
```bash
pip install numpy pandas scikit-learn
python run_pipeline.py
python demo.py
```

## Chaos scenario results
| Scenario | Path | Availability |
|---|---|---|
| CHAOS-01 Model Down | HEURISTIC_FALLBACK | maintained |
| CHAOS-02 FeatureStore Down | ML_MODEL (cached feats) | maintained |
| CHAOS-03 Corrupted Data | REJECTED | training_blocked |
| CHAOS-04 Stale Features | STALE_WARNING | maintained |
| CHAOS-05 NaN Output | HEURISTIC_FALLBACK | maintained |

nDCG@5: ML=0.9675 → fallback=0.9469 (delta -0.02: worse but working)
