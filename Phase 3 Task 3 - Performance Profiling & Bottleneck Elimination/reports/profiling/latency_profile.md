# Latency Profile Report — PlaceMux Inference Pipeline

**Task:** 3 — Performance Profiling & Bottleneck Elimination  
**Phase:** 3 · Sprint A  
**Date:** 2024-01-15  
**Samples:** 200 real-shaped requests per stage

---

## Pipeline Stages

```
Resume → resume_parse → feature_fetch → model_predict → db_lookup → api_serialise → Response
```

## Baseline Per-Stage Timings

| Stage | p50 (ms) | p95 (ms) | p99 (ms) | % of total p95 |
|---|---|---|---|---|
| resume_parse | 38 | 47 | 51 | 6% |
| **feature_fetch** | **200** | **508** | **700** | **65% ← BOTTLENECK** |
| model_predict | 28 | 35 | 36 | 4% |
| db_lookup | 65 | 172 | 221 | 22% |
| api_serialise | 12 | 15 | 17 | 2% |
| **TOTAL** | — | **776** | — | 100% |

**SLO status: BREACH** (target 500ms)

## Bottleneck: `feature_fetch`

- 65% of end-to-end p95
- Gamma-distributed latency — long tail to 700ms at p99
- Root cause: synchronous network call to remote feature store, zero caching

## Secondary: `db_lookup`

- 22% of p95  
- Sequential queries — parallelisable
