"""
Task 13 — Live Demo: predict.py
Shows single-record, batch, CSV scoring + edge cases via scoring interface.
"""
import sys, os, json, warnings
sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings('ignore')

from scoring.schema import CustomerInput, BatchInput
from scoring.scorer import score_single, score_batch, score_csv, _load_artifacts

_, _, meta = _load_artifacts()

print("\n" + "="*65)
print(f"  TASK 13 — LIVE DEMO: Model Score Extraction")
print(f"  Model Version : {meta['model_version']} | Hash: {meta['model_hash']}")
print(f"  Score Meaning : {meta['score_semantics']}")
print(f"  Threshold     : {meta['threshold']}")
print("="*65)

# ── Single scoring ──
print("\n── Single-Record Scoring ──")
customers = [
    ("Customer A (Low Risk)", CustomerInput(
        tenure=60, monthly_charges=45.0, total_charges=2700.0, num_products=4,
        support_calls=0, contract_type=2, payment_method=1, age_group=2,
        region=0, internet_service=1, online_backup=1, tech_support=1)),
    ("Customer B (High Risk)", CustomerInput(
        tenure=3, monthly_charges=105.0, total_charges=315.0, num_products=1,
        support_calls=7, contract_type=0, payment_method=3, age_group=0,
        region=2, internet_service=2, online_backup=0, tech_support=0)),
    ("Customer C (Medium Risk)", CustomerInput(
        tenure=18, monthly_charges=70.0, total_charges=1260.0, num_products=2,
        support_calls=2, contract_type=1, payment_method=2, age_group=1,
        region=1, internet_service=1, online_backup=0, tech_support=1)),
]
for name, cust in customers:
    r = score_single(cust, record_id=name)
    print(f"\n  {name}")
    print(f"  Score         : {r.score:.4f}")
    print(f"  Score Band    : {r.score_band}")
    print(f"  Prediction    : {r.prediction_label}")
    print(f"  Threshold Used: {r.threshold_used}")
    print(f"  Model Version : {r.model_version} | Hash: {r.model_hash}")
    print(f"  Scored At     : {r.scored_at}")

# ── Batch scoring ──
print("\n── Batch Scoring (3 records) ──")
batch = BatchInput(records=[c for _, c in customers], batch_id="live-demo-batch")
br = score_batch(batch)
print(f"  Batch ID  : {br.batch_id}")
print(f"  Scored    : {br.scored_records}/{br.total_records}")
print(f"  Failed    : {br.failed_records}")
print(f"  Version   : {br.model_version}")

# ── CSV batch ──
print("\n── CSV Batch Scoring (100 records) ──")
import pandas as pd
pd.read_csv('data/churn_data.csv').head(100).to_csv('/tmp/demo_batch.csv', index=False)
score_csv('/tmp/demo_batch.csv', '/tmp/demo_output.csv')
out = pd.read_csv('/tmp/demo_output.csv')
print(f"  Sample output row:")
print(out[['tenure','monthly_charges','churn_score','score_band','prediction_label','model_version']].head(3).to_string(index=False))

# ── Edge cases ──
print("\n── Edge Case Handling ──")
from pydantic import ValidationError as PydanticValidationError
edge_cases = [
    ("Empty input", {}),
    ("Out-of-range tenure=-5", dict(tenure=-5,monthly_charges=50,total_charges=600,num_products=2,support_calls=1,contract_type=1,payment_method=0,age_group=1,region=0,internet_service=1,online_backup=1,tech_support=0)),
    ("Unknown extra field", dict(tenure=12,monthly_charges=50,total_charges=600,num_products=2,support_calls=1,contract_type=1,payment_method=0,age_group=1,region=0,internet_service=1,online_backup=1,tech_support=0,unknown=99)),
]
for name, data in edge_cases:
    try:
        r = score_single(CustomerInput(**data))
        print(f"  {name}: scored {r.score:.4f}")
    except PydanticValidationError as e:
        msg = e.errors()[0]['msg']
        print(f"  {name}: ✓ Caught → {msg[:70]}")
    except Exception as e:
        print(f"  {name}: ✓ Error → {str(e)[:70]}")

print("\n" + "="*65)
print("  Demo complete. API: python scoring/api.py  (port 8000)")
print("="*65 + "\n")
