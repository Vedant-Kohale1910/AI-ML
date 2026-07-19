# Scaling Plan — PlaceMux Intelligence Layer (Task 4)

**Strategy:** Horizontal autoscale + precomputed hot-student scores

## Decision Matrix

| Strategy | Latency (hot) | Stale Risk | Complexity | Chosen |
|---|---|---|---|---|
| LRU cache only | ~50ms | None | Low | No |
| Horizontal autoscale | ≤465ms | None | Low | **Yes** |
| Score precompute | 4ms | 24h | Medium | Partial |
| **Autoscale + precompute** | **4ms (hot) / 465ms (cold)** | **24h (hot only)** | **Low-Medium** | **✓** |

## Autoscale Config

```yaml
hpa:
  metric: custom/inference_p95_latency
  scale_out_at: 400ms
  scale_in_at: 200ms (sustained 5min)
  min_replicas: 1
  max_replicas: 7
  warm_up_s: 90
```

## Replicas Required

| QPS | Replicas |
|---|---|
| ≤ 200 | 1 |
| 201-400 | 2 |
| 401-600 | 3 |
| 601-1000 | 5 |
| 1001+ | 7 |

## Precompute (Hot Students)

- Top 15% students by access → nightly Redis cache
- Covers ~22.6% of total request volume
- Latency: 4ms (Redis) vs 465ms (full pipeline)
- Refresh: 02:00 UTC nightly
