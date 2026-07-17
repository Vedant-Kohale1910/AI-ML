# Task 2 — Observability Deep-Dive, SLOs & Error Budgets
## PlaceMux Intelligence Layer · Phase 3 · Sprint A

**Status:** ✅ Production Ready  
**Version:** 1.0.0

---

## One-Sentence Goal

> *A model that is slow or silently returning garbage now pages someone before users notice.*

---

## What This Builds

| Deliverable | Description |
|---|---|
| **Inference SLOs** | p95 latency, availability, quality floors |
| **Monitoring + Alerts** | Live metrics; alerts on latency and score distribution |
| **Error Budget** | Documented monthly budget + burn-rate policy |

---

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python demo.py
```

---

## SLO Contract

```
Latency    p95 ≤ 500 ms      p99 ≤ 1 000 ms     p50 ≤ 120 ms
Availability  ≥ 99.9%        error rate ≤ 0.1%
Quality    precision ≥ 0.85  recall ≥ 0.80       FPR ≤ 0.15   F1 ≥ 0.825
Scores     std ≥ 0.05        range ≥ 0.20         (degenerate-output guard)

Error Budget   43.2 min / month   (30-day rolling)
```

---

## Alert Severity

| Severity | Trigger | Action |
|---|---|---|
| PAGE | Degenerate output, availability < 99%, p95 > 2× target | PagerDuty immediately |
| CRITICAL | Any SLO breached | Slack #ml-alerts, respond in 30 min |
| WARNING | Budget > 50% consumed | Slack #ml-ops, respond in 4 hrs |

---

## Demo — 7 Scenarios

```
python demo.py
```

| # | Scenario | Expected |
|---|---|---|
| 1 | Healthy baseline | ✅ All SLOs pass |
| 2 | Latency spike p95 > 500ms | 🚨 PAGE + CRITICAL |
| 3 | Quality degradation P/R below floor | 🔴 CRITICAL |
| 4 | Degenerate output (constant scores) | 🚨 PAGE |
| 5 | Availability crash (3% error rate) | 🚨 PAGE + CRITICAL |
| 6 | Error budget accounting | 📊 Budget report |
| 7 | Budget policy enforcement | 📋 Policy decision |

---

## Project Structure

```
Task2-SLO-Observability/
├── src/
│   ├── slo/
│   │   ├── definitions.py      # SLO targets + ErrorBudget dataclass
│   │   └── checker.py          # Per-SLO pass/fail evaluation
│   ├── monitoring/
│   │   └── metrics_collector.py # Rolling-window metric aggregation
│   ├── alerts/
│   │   └── alert_engine.py     # Alert rules, severity, routing
│   ├── error_budget/
│   │   └── tracker.py          # Incident logging + burn-rate calculation
│   └── simulation/
│       └── traffic_generator.py # Healthy + breach traffic generators
├── reports/
│   ├── slo/slo_contract.md
│   └── error_budget/error_budget_policy.md
├── demo.py                      # 7-scenario end-to-end demo
└── requirements.txt
```

---

## Integration with Previous Tasks

| Task | How Task 2 Connects |
|---|---|
| Task 17 (Recommendation Engine) | SLO quality floors enforce P/R/FPR from Task 17 |
| Task 9 (Hyperparameter Tuning) | Tuned model baseline sets quality SLO floor |
| Task 22 (Drift Monitoring) | Drift triggers quality SLO breach → alert |
| Task 23 (Model Registry) | Model version tagged in incident log |
| Task 25 (Live Monitoring) | Task 2 SLOs feed into Task 25 dashboard |

---

## Hand-Off to DevOps

Wire these metrics into the platform SLO dashboard:

```
inference_latency_p95_ms      CRITICAL alert ≥ 500
inference_availability_pct    PAGE alert < 99.0
model_precision               CRITICAL alert < 0.85
model_score_std               PAGE alert < 0.05
error_budget_pct_consumed     WARNING ≥ 50 / CRITICAL ≥ 75 / PAGE ≥ 100
```
