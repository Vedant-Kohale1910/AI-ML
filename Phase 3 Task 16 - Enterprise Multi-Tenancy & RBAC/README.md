# Task 16 — Enterprise Multi-Tenancy & RBAC
PlaceMux · Phase 3 · Sprint D

## Run
```bash
pip install numpy pandas scikit-learn pyyaml
python run_pipeline.py
python demo.py
```

## Key results
- 3 tenants (google, microsoft, amazon) with isolated data partitions
- 6 cross-tenant leakage tests: ALL PASS
- Per-tenant configs: google threshold=0.55, microsoft=0.40, amazon=0.50
- Zero code forks — same run path, different configs/data
- Failure: unknown tenant → PermissionError; missing config → default.yaml fallback
