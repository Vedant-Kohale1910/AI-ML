# Task 20 — Enterprise Readiness Integration & Pilot Dry-Run
PlaceMux · Phase 3 · Sprint D

## Run
```bash
pip install numpy pandas scikit-learn
python run_pipeline.py
python demo.py
```

## Pilot results (Google, 30 candidates, 12 roles)
| Metric | Target | Pilot | Pass |
|---|---|---|---|
| Precision@5 | ≥0.60 | 0.45 | ✗ → remediation |
| nDCG@5 | ≥0.70 | 0.73 | ✓ |
| DPD | <0.15 | 0.175 | ✗ → IPS calibration |
| Latency p95 | <200ms | 0.33ms | ✓ |

## Decision: CONDITIONAL PASS — 3 HIGH-priority remediations before production
