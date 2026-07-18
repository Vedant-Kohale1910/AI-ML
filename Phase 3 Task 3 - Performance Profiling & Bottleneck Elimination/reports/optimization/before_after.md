# Before / After Optimization Report

**Strategy:** LRU Feature Cache + Parallel Async DB Queries  
**Date:** 2024-01-15

---

## Summary

| Metric | Before | After | Change |
|---|---|---|---|
| p95 latency | 776ms | 465ms | **-40%** |
| Serving cost | ₹89/day | ₹53/day | **-40%** |
| Precision@5 | 0.809 | 0.838 | +0.029 (within tolerance) |
| nDCG@5 | 0.832 | 0.847 | +0.015 (within tolerance) |
| SLO (500ms) | **BREACH** | **✅ MET** | |

## Optimizations Applied

### 1. LRU Feature Cache
- Cache hit rate: 82%
- Hit latency: 8ms (vs 200ms+ cold)
- Memory: ~120MB for 50k vectors
- Invalidation: on skill-update event

### 2. Parallel Async DB Queries
- Parallelism factor: 0.45 (55% reduction in db_lookup)
- Requires connection pool ≥ 20

## Quality Verification (held-out n=200 queries)

All metrics improved slightly (cache serves fresh data faster).  
Maximum drop: 0.000 — within 0.02 tolerance.  
Quality acceptable: **YES**

## Design Decisions

**Chosen:** cache + parallel-DB  
**Rejected:** score precompute — 24h staleness not acceptable  
**Rejected:** model quantisation — saves only ~6ms
