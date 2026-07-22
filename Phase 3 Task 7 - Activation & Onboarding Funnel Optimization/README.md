# Task 7 — Activation & Onboarding Funnel Optimization
## Cold-Start Recommendations · Phase 3 · Sprint B

**The bar:** A brand-new candidate sees genuinely relevant jobs in their first session.

## Quick Start
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python demo.py
```

## Results
| Metric | Baseline (popular) | Cold-Start | Lift |
|---|---|---|---|
| CTR | 12% | 20% | +67% |
| Apply rate | 8% | 13% | +68% |
| Precision@5 | 0.79 | 0.89 | +13% |

## Design Decision
- **Chosen:** Content-based (skill-match) + 30% exploration
- **Rejected:** Pure popularity — ignores stated skills
- **Rejected:** Onboarding quiz — adds friction, lowers activation

## Demo Sections
| Section | Content |
|---|---|
| A | Fresh account — cold-start detection |
| B | 5 recommendations with plain-English explanations |
| C | Lift metrics vs popularity baseline |
| D | 70/30 exploitation/exploration breakdown |
| E | Model failure → fallback never empty |
| F | Post-first-click personalization |

## Structure
```
src/
  recommendation/engine.py        # Phase 2 engine
  cold_start/onboarding_engine.py # Cold-start + fallback
data/
  students.csv  (800 students)
  jobs.csv      (80 jobs)
demo.py
```

## Hand-off
- API: `GET /api/recommendations/cold-start?student_id=NEW-001`
- Trigger: `clicks==0 AND applications==0` at session start
- Fallback: popularity prior, always non-empty
