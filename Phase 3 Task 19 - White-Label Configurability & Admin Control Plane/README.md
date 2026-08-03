# Task 19 — White-Label Configurability & Admin Control Plane
PlaceMux · Phase 3 · Sprint D

## Run
```bash
pip install numpy pandas scikit-learn
python run_pipeline.py
python demo.py
```

## Key deliverables
- Per-tenant JSON policy files (configs/)
- 5 guardrail validation tests: all rejected correctly
- Admin preview before deployment (old vs new ranking diff)
- Hard guardrail blocks bad deploy in failure scenario

## Design decisions
- Rules on top of model (not retraining per tenant): instant, auditable, bounded
- Hard guardrails over warnings: warnings get dismissed in hiring AI
