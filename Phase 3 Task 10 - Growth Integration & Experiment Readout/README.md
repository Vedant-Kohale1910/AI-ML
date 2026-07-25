# Task 10 — Growth Integration & Experiment Readout
## PlaceMux · Phase 3 · Sprint B

**The bar:** A decision made on evidence — including the discipline to kill your own model if it lost.

## Quick Start
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python demo.py
```

## Results
| Metric | V1 | V2 | Status |
|---|---|---|---|
| CTR | 13.4% | 18.8% | +40.5% lift |
| Apply rate | 9.5% | 13.4% | +41% lift |
| Hire precision | 0.882 | 0.881 | ✓ above floor |
| Guardrails | — | ALL PASS | ✅ |
| **Decision** | | | **SHIP ✅** |

## Three Deliverables
- **Stage B** — Pre-registered A/B (hypothesis written before seeing results)
- **Stage C** — Honest readout: z-test, p-value, effect size, 95% CI, guardrails
- **Stage D** — Ship / Do-Not-Ship with evidence-based reasoning
