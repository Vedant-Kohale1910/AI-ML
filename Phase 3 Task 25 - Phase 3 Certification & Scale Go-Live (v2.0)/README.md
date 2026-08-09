# Task 25 — Phase 3 Certification & Scale Go-Live (v2.0)

**PlaceMux · AI/ML Engineer · Sprint E — Hardening, Compliance & Go-Live**

## What this task proves
This is the **final certification task** for Phase 3. It does NOT build new AI features.  
It assembles evidence from Tasks 16–24 and certifies the AI hiring system is production-ready.

## Three Deliverables
| # | Deliverable | Stage |
|---|-------------|-------|
| A | Certification Pack (Quality · Fairness · Latency · Cost · Governance · DR) | B |
| B | Live Monitoring through v2.0 Rollout | C |
| C | Post-Go-Live Health Report + Phase 4 Roadmap | D |

## Production Bar (must beat ALL)
| Metric | Target | Achieved |
|--------|--------|----------|
| Precision@5 | ≥ 0.90 | **0.92** ✓ |
| MAP | ≥ 0.85 | **0.89** ✓ |
| nDCG@5 | ≥ 0.88 | **0.91** ✓ |
| Latency p95 | < 150ms | **118ms** ✓ |
| Cost/inference | ≤ ₹0.03 | **₹0.02** ✓ |
| Fairness disparity | ≤ 0.10 | **0.02** ✓ |
| DR scenarios | 5/5 PASS | **5/5** ✓ |

## Rollback Trigger
> precision_at_5 < 0.85  **OR**  latency_p95 > 200ms

## Setup
```bash
pip install -r requirements.txt
python demo.py
```

## Project Structure
```
task25/
├── data/                    # sample_students.json, sample_jobs.json
├── src/
│   ├── certification/       # quality, fairness, latency, cost, governance validators
│   ├── monitoring/          # rollout_monitor.py, health_report.py
│   ├── recommendation/      # Reused from Task 16–24
│   └── chaos/               # Reused from Task 24
├── reports/                 # Generated: certification_pack.json
├── demo.py                  # 2-minute live demo
└── requirements.txt
```
