# Task 9 — Experimentation Platform, Feature Flags & Guardrails
## PlaceMux · Phase 3 · Sprint B

**The bar:** Ship v2 to 10% of traffic and know within days whether it's better or worse.

## Quick Start
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python demo.py
```

## Results
| Metric | V1 | V2 | Decision |
|---|---|---|---|
| CTR | 13.8% | 15.8% | +14.5% ↑ |
| Apply rate | 9.5% | 11.2% | +18% ↑ |
| Precision@5 | 0.905 | 0.912 | +0.8% ↑ |
| Guardrails | — | ALL PASS | ✅ SHIP |

## Structure
| Module | Purpose |
|---|---|
| `VariantRouter` | Hash-based consistent assignment (80/10/10) |
| `HoldoutManager` | Permanent 10% holdout — never gets new model |
| `GuardrailChecker` | Auto-halt on CTR drop, precision floor, SLO, fairness |
| `RollbackManager` | Routes all v2 traffic to v1 in 3ms |

## Design Decisions
- **Assignment**: Hash-based (rejected: random per-request → users flip → invalid)
- **Holdout**: Permanent (rejected: switchback → confounds long-term measurement)
- **Guardrails**: Hard halt on CTR >5% drop, hire precision <85%, or SLO breach
