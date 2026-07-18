# Task 3 — Performance Profiling & Bottleneck Elimination
## PlaceMux Intelligence Layer · Phase 3 · Sprint A

**Status:** ✅ Complete  
**SLO (500ms p95):** ✅ Met (465ms)  
**Quality drop:** ✅ Within 0.02 tolerance on all metrics

---

## One-Sentence Goal

> Profile the inference path, identify the bottleneck, and cut p95 latency to ≤ 500ms (Task 2 SLO) with ≤ 0.02 absolute quality drop on held-out data.

---

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python demo.py
```

---

## Results

| Metric | Before | After | Change |
|---|---|---|---|
| p95 latency | 776ms | 465ms | **−40%** |
| Serving cost | ₹89/day | ₹53/day | **−40%** |
| Precision@5 | 0.809 | 0.838 | +0.029 ✓ |
| nDCG@5 | 0.832 | 0.847 | +0.015 ✓ |
| **SLO (500ms)** | BREACH | **✅ MET** | |

---

## Bottleneck

`feature_fetch` — 65% of end-to-end p95 (remote feature store, no caching).

## Strategy Chosen

**LRU Feature Cache + Parallel Async DB Queries**

- Cache hit rate 82% → 8ms vs 200ms+ cold path
- Parallel DB queries → 55% reduction in `db_lookup`
- Combined: 776ms → 465ms (−40%)

**Rejected:**
- Score precompute — 24h staleness unacceptable for active job seekers
- Model quantisation — saves only ~6ms (not the bottleneck)

---

## Demo — 6 Sections

```
python demo.py
```

| Section | Content |
|---|---|
| A | Baseline latency profile — 5 stages, 200 requests |
| B | Bottleneck identified: feature_fetch (65% of p95) |
| C | 3 strategies benchmarked; chosen meets SLO |
| D | Before/after: latency, cost, quality |
| E | 3 failure scenarios injected and verified |
| F | Worked example: Aarav → ML Engineer, 119ms p50 |

---

## Project Structure

```
Task3-Profiling/
├── src/
│   ├── profiler/
│   │   └── pipeline_profiler.py      # Per-stage timing, PipelineProfile
│   ├── optimizer/
│   │   └── optimizations.py          # 3 strategies + FullOptimizedProfiler
│   ├── quality/
│   │   └── quality_guard.py          # Precision@k, nDCG@k, MAP, tolerance check
│   ├── simulation/
│   │   └── failure_injection.py      # 3 failure modes with recovery paths
│   └── reporting/
│       └── report_builder.py         # Before/after tables and cost estimates
├── reports/
│   ├── profiling/latency_profile.md
│   ├── optimization/before_after.md
│   └── quality/quality_report.md
├── demo.py
└── requirements.txt
```

---

## Connection to Previous Tasks

| Task | Connection |
|---|---|
| Task 2 (SLOs) | 500ms p95 SLO defined there; Task 3 meets it |
| Task 17 (Recommendation Engine) | Profiled pipeline is Task 17's serving path |
| Task 9 (Hyperparameter Tuning) | Tuned model is the inference target |
| Task 23 (Model Registry) | Optimised serving path registered as new config |
| Task 25 (Live Monitoring) | Latency metrics feed Task 25 dashboard |

---

## Hand-off to Backend / DevOps

```
inference_latency_p95_ms → Task 2 SLO dashboard
Cache warm-up job        → runs at deploy time (avoids cold-start breach)
DB connection pool       → increase to ≥ 20 for parallel async queries
```
