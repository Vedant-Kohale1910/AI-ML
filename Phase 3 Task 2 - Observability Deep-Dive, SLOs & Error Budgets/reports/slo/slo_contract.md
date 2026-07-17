# SLO Contract — PlaceMux Intelligence Layer

**Version:** 1.0  **Owner:** ML-Ops  **Reviewed:** 2024-01-15

---

## What "Good" Means Here

> *A model that is slow or silently returning garbage now pages someone before users notice.*

---

## Inference SLOs

| Metric | Target | Alert Level |
|---|---|---|
| p50 latency | ≤ 120 ms | — |
| p95 latency | ≤ 500 ms | CRITICAL |
| p99 latency | ≤ 1 000 ms | WARNING |
| Availability | ≥ 99.9% | CRITICAL / PAGE |
| Error rate | ≤ 0.1% | CRITICAL |
| Precision | ≥ 0.85 | CRITICAL |
| Recall | ≥ 0.80 | CRITICAL |
| FPR | ≤ 0.15 | CRITICAL |
| F1 | ≥ 0.825 | CRITICAL |
| Score std-dev | ≥ 0.05 | **PAGE** (degenerate output) |
| Score range | ≥ 0.20 | **PAGE** (degenerate output) |

## Error Budget

| Item | Value |
|---|---|
| SLO | 99.9% availability |
| Monthly Budget | **43.2 minutes** |
| 50% consumed | Review cadence |
| 75% consumed | Halt experiments |
| 100% consumed | FREEZE deploys |

## Alert Routing

```
PAGE     → #ml-incidents → PagerDuty
CRITICAL → #ml-alerts (30 min SLA)
WARNING  → #ml-ops (4 hr SLA)
```
