# Load Test Report — PlaceMux Intelligence Layer (Task 4)

**Date:** 2024-01-15 | **Data:** 800 students, 80 jobs (Phase 2) | **SLO:** 500ms p95

## Results

| QPS | p50 ms | p95 ms | p99 ms | Throughput | Error% | SLO |
|---|---|---|---|---|---|---|
| 10  | 117 | 275 | 360 | 10.0 | 0.0% | ✅ |
| 50  | 124 | 283 | 348 | 50.0 | 0.0% | ✅ |
| 100 | 141 | 306 | 466 | 100.0 | 0.0% | ✅ |
| 150 | 184 | 432 | 569 | 150.0 | 0.0% | ✅ |
| 200 | 242 | **499** | 700 | 200.0 | 0.0% | ✅ |
| 300 | 716 | **1594** | 1738 | 299.9 | 0.0% | 🚨 |
| 500 | 1669 | 1867 | 1905 | 465.2 | 7.0% | 🚨 |

## Breaking Point

- **Safe capacity:** 200 QPS (p95 = 499ms — just under 500ms SLO)
- **Breaking point:** 300 QPS (p95 jumps to 1594ms — 3× SLO breach)
- **Scale-out trigger:** 400ms (20% headroom before SLO breach)

## Latency Model

Calibrated from Task 3 profiling results using M/M/1 queuing theory:
- Single-replica capacity: 350 QPS
- At 70% utilisation (245 QPS): p95 ≈ 400ms
- At 86% utilisation (300 QPS): p95 > 500ms (SLO breach)
