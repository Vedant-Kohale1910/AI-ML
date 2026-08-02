# Task 18 — SSO, SCIM & Enterprise Identity
PlaceMux · Phase 3 · Sprint D

## Run
```bash
pip install numpy pandas scikit-learn
python run_pipeline.py
python demo.py
```

## Key results
- Recruiter + org scoped signals: R001 gets +0.15 recruiter boost, +0.075 org boost
- Mover R001: score drops from 1.0 → 0.889 after google→microsoft move (instant swap)
- Leaver R002: 3 recruiter signals archived, org signals retained, post-deprovision access blocked
- 4 isolation tests: ALL ISOLATED (0 signals exposed cross-org)
