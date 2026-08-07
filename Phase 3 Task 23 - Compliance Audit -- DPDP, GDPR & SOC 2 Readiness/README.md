# Task 23 — Compliance Audit: DPDP, GDPR & SOC 2 Readiness
PlaceMux · Phase 3 · Sprint E

## Run
```bash
pip install numpy pandas scikit-learn
python run_pipeline.py
python demo.py
```

## Results: 9/9 compliance checks pass
- Data minimisation: email/phone/aadhaar dropped from feature store at ingestion
- Right of Access (DPDP §12): 0 PII fields in feature store ✓
- Right to Delete (DPDP §17): feature store immediate, data store 90d window ✓
- Automated-decision disclosure (DPDP §16): notice + human review ticket on every recommendation ✓
- Human review SLA: 5 business days, named reviewer ✓
