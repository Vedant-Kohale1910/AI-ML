# Error Budget Policy — PlaceMux Intelligence Layer

**Owner:** ML-Ops  **Period:** Monthly (30 days)  **Budget:** 43.2 min

---

## Calculation

```
Budget = (1 - availability_SLO) × minutes_in_month
       = (1 - 0.999) × 43,200
       = 43.2 minutes / month
```

## Burn Rate Definition

| Rate | Meaning |
|---|---|
| 1.0× | On track to exactly consume budget |
| 2.0× | Budget will be exhausted in 15 days |
| 5.0× | Budget will be exhausted in 6 days |

## Policy

| Budget Consumed | Freeze Releases | Halt Experiments | Accelerate Retrain |
|---|---|---|---|
| 0–50% | No | No | No |
| 50–75% | No | No | Yes |
| 75–100% | No | Yes | Yes |
| 100%+ | **YES** | **YES** | **YES** |

## Incident Categories

- **latency** — p95 above SLO threshold
- **quality** — precision/recall below SLO floor
- **degenerate_output** — model returning constant/near-constant scores
- **availability** — error rate above SLO threshold
