# Task 4 — Horizontal Scale & Load Readiness
## PlaceMux Intelligence Layer · Phase 3 · Sprint A

**Status:** ✅ Complete | **Real data:** 800 students, 80 jobs (Phase 2)

---

## The Bar (stated before building)

> "Know the exact QPS where p95 breaches 500ms SLO, have a scaling plan ready,
> and guarantee students always receive recommendations even when the ML model is down."

---

## Results

| Deliverable | Result |
|---|---|
| Safe QPS (single replica) | **200 QPS** |
| Breaking point | **300 QPS** (p95 = 1594ms) |
| Scaling strategy | Autoscale + precompute hot students |
| Fallback | 3-tier: ML → heuristic → cache |
| Online/offline gap | All metrics within 0.03 tolerance |
| Fairness | Max disparity 3.4% (threshold 10%) |

---

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python demo.py
```

---

## Demo — 7 Sections

| Section | Content |
|---|---|
| A | Load test: 10 QPS levels, latency table with SLO status |
| B | Breaking point: 300 QPS; safe capacity: 200 QPS |
| C | Scaling plan: autoscale thresholds + precompute eligibility |
| D | Fallback: Tier 1 (ML), Tier 2 (heuristic), Tier 3 (cache) |
| E | Online validation: offline→online gap < 0.03 |
| F | Continuous fairness: per-group precision, max 3.4% disparity |
| G | Model card: purpose, limitations, responsible use |

---

## Project Structure

```
Task4-ScaleLoadReadiness/
├── src/
│   ├── recommendation/engine.py         # Phase 2 engine (real data schema)
│   ├── load_test/load_tester.py         # QPS sweep, M/M/1 latency model
│   ├── fallback/fallback_engine.py      # 3-tier + circuit breaker
│   ├── scaling/scaling_plan.py          # Autoscale + precompute plan
│   ├── online_validation/validator.py   # Offline/online comparison, fairness
│   └── governance/model_card.py         # Model card generation
├── data/
│   ├── students.csv                     # 800 students (Phase 2)
│   └── jobs.csv                         # 80 jobs (Phase 2)
├── reports/
│   ├── load_test/load_test_report.md
│   └── scaling/scaling_plan.md
├── demo.py
└── requirements.txt
```

---

## Connection to Previous Tasks

| Task | Connection |
|---|---|
| Task 2 (SLOs) | 500ms p95 SLO; scale-out trigger at 400ms (20% headroom) |
| Task 3 (Profiling) | Capacity 350 QPS/replica from profiling; latency model calibrated |
| Task 9 (Tuning) | v1.3-tuned model is the inference target |
| Task 23 (Registry) | Model version v1.3-tuned tracked |
| Task 25 (Monitoring) | Latency + fairness metrics feed live dashboard |

---

## Hand-Off to DevOps

```
K8s HPA metric   : custom/inference_p95_latency
Scale-out at     : p95 > 400ms
Scale-in at      : p95 < 200ms (5 min sustained)
Min/max replicas : 1 / 7
Redis cluster    : Required for hot-student precomputed scores
Circuit breaker  : 5% error rate → OPEN, 30s cool-down
Cold-start       : Warm-up job at deploy time
```
