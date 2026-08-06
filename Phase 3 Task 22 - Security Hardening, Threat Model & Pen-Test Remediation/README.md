# Task 22 — Security Hardening, Threat Model & Pen-Test Remediation
PlaceMux · Phase 3 · Sprint E

## Run
```bash
pip install numpy pandas scikit-learn
python run_pipeline.py
python demo.py
```

## Results
| Attack | Detected | Action |
|---|---|---|
| Keyword stuffing (10× repeat) | ✓ | DOWN_RANKED (0.889→0.32) |
| Prompt injection | ✓ | BLOCKED (score=0) |
| Data poisoning (novel skill flood) | ✓ | QUARANTINE |
| Model extraction (51 unique pairs) | ✓ | BLOCK |
