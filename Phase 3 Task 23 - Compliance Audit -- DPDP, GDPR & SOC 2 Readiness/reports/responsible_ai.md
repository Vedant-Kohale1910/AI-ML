# Responsible AI Report — Task 23

## Model card
- Model: reco-v2.0
- PII in model features: [] (empty = compliant)
- Human review: True

## Fairness results
- experience_tier: DPD after=0.09 pass=True
- assessment_tier: DPD after=0.24 pass=?

## Lineage
- training_data_source: data/event_logs.csv (Task-6 logs)
- feature_computation: src/recommendation/feature_engineering.py
- reproducible: True
- seed: 42
- pipeline: run_pipeline.py

## Decision: Deletion without retraining vs retraining
Documented retention window (90 days) chosen over immediate retraining.
Retraining per deletion is O(N) compute, impractical in production.
GDPR Recital 26 and DPDP §17 permit documented retention windows.
