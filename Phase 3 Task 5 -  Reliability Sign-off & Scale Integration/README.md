# Task 5 — Reliability Sign-off & Scale Integration
## PlaceMux Intelligence Layer · Phase 3 · Sprint A

**Status:** ✅ PASS  
**Model:** v1.3-tuned  
**Data:** 800 students, 80 jobs (Phase 2 real dataset)

---

## The Bar

> "Matching stays correct, fast and observable under sustained realistic load —  
> and a student always receives recommendations even when the model is down."

---

## Verdict: PASS ✅

| Criterion | Target | Actual |
|---|---|---|
| p95 latency | ≤ 500ms | 499ms @ 200 QPS |
| Availability | ≥ 99.9% | 100% (0 errors) |
| Precision | ≥ 0.85 | 0.91 |
| Recall | ≥ 0.80 | 0.89 |
| Fallback | Always serves | ✅ 3/3 scenarios |
| Fairness disparity | < 10% | 3.4% max |
| Online/offline gap | < 0.03 | 0.022 max |

---

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python demo.py
```

---

## Sprint-A Integration

| Task | Contribution to Task 5 |
|---|---|
| Task 2 | SLO contract (500ms, 99.9%, quality floors) |
| Task 3 | 350 QPS/replica capacity; cache+parallel-DB optimisation |
| Task 4 | 200 QPS safe / 250 QPS breaking point; 3-tier fallback |
| **Task 5** | End-to-end integration, failure injection, PASS certificate |

---

## Demo — 8 Sections

```
python demo.py
```

| Section | What It Shows |
|---|---|
| A | Integrated pipeline: Arnav Suri → Business Analyst recommendations |
| B | Load test: 10 QPS levels, breaking point at 250 QPS |
| C | SLO check: all four dimensions PASS |
| D | 3 failure scenarios injected; fallback always serves |
| E | Monitoring snapshot: p95, scores, error rate |
| F | Online vs offline: all gaps within 0.03 tolerance |
| G | Fairness: 7 groups, max 3.4% disparity |
| H | Formal sign-off certificate: **PASS ✅** |

---

## Structure

```
Task5-ReliabilitySignoff/
├── src/
│   ├── recommendation/engine.py          # Phase 2 engine (Task 17 schema)
│   ├── reliability/slo_checker.py        # Task 2 SLO contract evaluation
│   ├── reliability/load_test.py          # QPS sweep, latency model
│   ├── reliability/failure_injection.py  # 3 deliberate break scenarios
│   ├── fallback/engine.py                # 3-tier + degenerate guard
│   ├── monitoring/monitor.py             # Rolling window + fairness
│   └── governance/signoff.py             # Formal certificate + residual risks
├── data/
│   ├── students.csv                      # 800 students (Phase 2)
│   └── jobs.csv                          # 80 jobs (Phase 2)
├── reports/
│   └── reliability_signoff.md
├── demo.py
└── requirements.txt
```

---

## Residual Risks (Accepted)

1. Skill matching is lexical — alias gaps may misclassify near-synonyms
2. Hot-student precompute cache can be up to 24h stale
3. Cold-start replica breach window ~90s at burst scale-up
4. DPDP consent gate not yet wired to recommendation suppression
5. Fairness audit covers 7 groups; intersections not yet measured

---

## Hand-off to DevOps / Growth

```
K8s HPA metric   : custom/inference_p95_latency
Scale-out at     : p95 > 400ms
Min/max replicas : 1 / 7
Circuit breaker  : 5% error rate → OPEN, 30s cool-down
SLO dashboard    : Task 2 contract; alerts already wired
Next review      : 2024-04-15
```
