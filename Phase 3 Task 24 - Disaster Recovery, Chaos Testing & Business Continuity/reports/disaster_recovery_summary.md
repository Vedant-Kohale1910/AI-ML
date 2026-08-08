# Disaster Recovery Summary — Task 24

## SLO targets
- Recommendation availability: >99.9% (never 0 results)
- Fallback engagement: <50ms
- Incident detection: <5s
- MTTR: <30 min (model), <15 min (feature store)

## Chaos scenario results

| Scenario | Path | Availability | Degraded |
|---|---|---|---|
| NORMAL | ML_MODEL | maintained | False |
| CHAOS-01 Model Down | HEURISTIC_FALLBACK | maintained | True |
| CHAOS-02 FeatureStore Down | ML_MODEL | maintained | False |
| CHAOS-03 Corrupted Data | REJECTED | training_blocked | False |
| CHAOS-04 Stale Features | STALE_WARNING | maintained | True |
| CHAOS-05 NaN Model Output | HEURISTIC_FALLBACK | maintained | True |

## Quality impact (held-out data)
| Mode | nDCG@5 | Notes |
|---|---|---|
| Normal (ML model) | 0.9675 | Full feature scoring |
| Fallback (heuristic) | 0.9469 | Skill-overlap only |
| Delta | -0.0206 | Worse but working |

## Design decision
Fail-OPEN (heuristic) for candidate-facing surfaces.
Fail-CLOSED (reject batch) for training data pipeline.
Automated fallback; manual recovery guided by runbook.
