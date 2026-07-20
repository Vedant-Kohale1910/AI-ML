# Reliability Sign-off Report — PlaceMux Intelligence Layer

**Date:** 2024-01-15  
**Model:** v1.3-tuned  
**Dataset:** 800 students, 80 jobs (Phase 2)  
**Verdict:** PASS ✅

## SLO Results

| SLO | Target | Actual | Status |
|---|---|---|---|
| p95 latency | ≤ 500ms | 499ms @ 200 QPS | ✅ |
| Availability | ≥ 99.9% | 100% | ✅ |
| Precision | ≥ 0.85 | 0.91 | ✅ |
| Recall | ≥ 0.80 | 0.89 | ✅ |
| FPR | ≤ 0.15 | 0.08 | ✅ |
| Score std | ≥ 0.05 | 0.13 | ✅ |

## Load Test

- Safe QPS (single replica): 200
- Breaking point: 250 QPS
- Scaling plan: autoscale at p95 > 400ms (Task 4)

## Failure Injection Results

| Scenario | Tier Served | Student Got Recs |
|---|---|---|
| Model pod crash | Tier 2 (heuristic) | ✅ |
| Feature store down | Tier 1 (stale) | ✅ |
| Degenerate output | Tier 2 (heuristic) | ✅ |

## Fairness (7 groups)

Max disparity: 3.4% — within 10% threshold. All groups acceptable.

## Residual Risks

5 risks accepted and documented in sign-off certificate.

## Baseline vs Production

| Metric | Baseline | Production | Change |
|---|---|---|---|
| Precision | 0.72 | 0.91 | +26% |
| Recall | 0.70 | 0.89 | +27% |
| p95 latency | 776ms | 465ms | -40% |
