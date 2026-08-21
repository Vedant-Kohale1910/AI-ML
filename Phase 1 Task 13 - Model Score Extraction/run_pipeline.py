"""
Task 13 — Model Score Extraction
Main pipeline: train model → build scoring interface → validate → batch score → demo API
"""
import sys, os, json, warnings, time
sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

print("="*65)
print("  TASK 13 — MODEL SCORE EXTRACTION PIPELINE")
print("="*65)

# ── STEP 1: Train & save versioned model ──
print("\n[STEP 1] Training and saving versioned model...")
from src.train_model import train_and_save
model, scaler, meta = train_and_save('data/churn_data.csv', 'models')
print(f"  Version  : {meta['model_version']}")
print(f"  Hash     : {meta['model_hash']}")
print(f"  Trained  : {meta['trained_at']}")
print(f"  Threshold: {meta['threshold']} | Score: {meta['score_semantics']}")

# ── STEP 2: Define input contract ──
print("\n[STEP 2] Input contract defined via Pydantic schema:")
from scoring.schema import CustomerInput, BatchInput, score_band
print("  14 typed, range-validated features (see scoring/schema.py)")
print("  Output: score, score_band, prediction_label, model_version, model_hash, scored_at")

# ── STEP 3: Single-record scoring ──
print("\n[STEP 3] Single-record scoring interface demo...")
from scoring.scorer import score_single, score_batch, score_csv

samples = [
    ("Customer A — Low Risk", CustomerInput(
        tenure=60, monthly_charges=45.0, total_charges=2700.0, num_products=4,
        support_calls=0, contract_type=2, payment_method=1, age_group=2,
        region=0, internet_service=1, online_backup=1, tech_support=1)),
    ("Customer B — High Risk", CustomerInput(
        tenure=3, monthly_charges=105.0, total_charges=315.0, num_products=1,
        support_calls=7, contract_type=0, payment_method=3, age_group=0,
        region=2, internet_service=2, online_backup=0, tech_support=0)),
    ("Customer C — Medium Risk", CustomerInput(
        tenure=18, monthly_charges=70.0, total_charges=1260.0, num_products=2,
        support_calls=2, contract_type=1, payment_method=2, age_group=1,
        region=1, internet_service=1, online_backup=0, tech_support=1)),
]

print(f"\n  {'Customer':<28} {'Score':>7} {'Band':<14} {'Label':<10} {'Version'}")
print(f"  {'-'*75}")
for name, cust in samples:
    t0 = time.perf_counter()
    result = score_single(cust, record_id=name.replace(' ','_'))
    latency = (time.perf_counter() - t0) * 1000
    print(f"  {name:<28} {result.score:>7.4f} {result.score_band:<14} {result.prediction_label:<10} {result.model_version}  ({latency:.1f}ms)")

# ── STEP 4: Batch scoring (in-memory) ──
print("\n[STEP 4] Batch scoring (in-memory) — 3 records...")
batch = BatchInput(records=[c for _, c in samples], batch_id="demo-batch-001")
batch_result = score_batch(batch)
print(f"  Batch ID     : {batch_result.batch_id}")
print(f"  Total        : {batch_result.total_records}")
print(f"  Scored       : {batch_result.scored_records}")
print(f"  Failed       : {batch_result.failed_records}")
print(f"  Model version: {batch_result.model_version}")
print(f"  Scored at    : {batch_result.scored_at}")

# ── STEP 5: Batch CSV scoring ──
print("\n[STEP 5] Batch CSV file scoring (500 records)...")
df_full = pd.read_csv('data/churn_data.csv').head(500)
df_full.to_csv('data/batch_input.csv', index=False)
scored_df = score_csv('data/batch_input.csv', 'results/batch_scores_output.csv')
print(f"  Score distribution:")
print(scored_df['score_band'].value_counts().to_string())

# ── STEP 6: Score distribution plot ──
print("\n[STEP 6] Generating score distribution plots...")
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].hist(scored_df['churn_score'], bins=30, color='steelblue', edgecolor='white')
axes[0].axvline(meta['threshold'], color='red', linestyle='--', label=f"Threshold={meta['threshold']}")
axes[0].set_xlabel('Churn Score'); axes[0].set_ylabel('Count')
axes[0].set_title('Score Distribution (Batch CSV)'); axes[0].legend()
band_counts = scored_df['score_band'].value_counts()
colors = {'LOW':'#27ae60','MEDIUM-LOW':'#f39c12','MEDIUM-HIGH':'#e67e22','HIGH':'#e74c3c'}
axes[1].bar(band_counts.index, band_counts.values, color=[colors.get(b,'gray') for b in band_counts.index])
axes[1].set_xlabel('Score Band'); axes[1].set_ylabel('Count')
axes[1].set_title('Score Band Distribution')
plt.tight_layout()
plt.savefig('results/plots/score_distribution.png', dpi=100); plt.close()
print("  Plot saved: results/plots/score_distribution.png")

# ── STEP 7: Validate edge cases ──
print("\n[STEP 7] Edge-case & input validation test...")
from pydantic import ValidationError as PydanticValidationError

edge_tests = [
    ("Missing field", {'tenure': 12}),
    ("Out-of-range tenure (-1)", {'tenure':-1,'monthly_charges':50,'total_charges':600,'num_products':2,'support_calls':1,'contract_type':1,'payment_method':0,'age_group':1,'region':0,'internet_service':1,'online_backup':1,'tech_support':0}),
    ("Invalid type (string)", {'tenure':'abc','monthly_charges':50,'total_charges':600,'num_products':2,'support_calls':1,'contract_type':1,'payment_method':0,'age_group':1,'region':0,'internet_service':1,'online_backup':1,'tech_support':0}),
    ("Extra unknown field", {'tenure':12,'monthly_charges':50,'total_charges':600,'num_products':2,'support_calls':1,'contract_type':1,'payment_method':0,'age_group':1,'region':0,'internet_service':1,'online_backup':1,'tech_support':0,'unknown_field':99}),
]
for name, data in edge_tests:
    try:
        rec = CustomerInput(**data)
        r = score_single(rec)
        print(f"  {name}: SCORED {r.score:.4f}")
    except PydanticValidationError as e:
        errs = [err['msg'] for err in e.errors()]
        print(f"  {name}: ✓ Caught → {errs[0][:70]}")
    except Exception as e:
        print(f"  {name}: ✓ Error → {str(e)[:70]}")

# ── STEP 8: Measure latency ──
print("\n[STEP 8] Latency benchmark (100 single calls)...")
import time
cust = samples[0][1]
times = []
for _ in range(100):
    t0 = time.perf_counter()
    score_single(cust)
    times.append((time.perf_counter()-t0)*1000)
print(f"  Mean: {np.mean(times):.2f}ms | P95: {np.percentile(times,95):.2f}ms | P99: {np.percentile(times,99):.2f}ms")

# ── STEP 9: Save interface documentation ──
print("\n[STEP 9] Saving interface documentation...")
interface_doc = {
    "interface_version": "1.0.0",
    "endpoints": {
        "GET /health": "Health check + model version",
        "GET /model/info": "Full model metadata",
        "POST /score/single": "Score one customer record",
        "POST /score/batch": "Score up to 10,000 records"
    },
    "input_contract": {k: str(v) for k, v in CustomerInput.schema()['properties'].items()},
    "output_contract": {
        "score": "float 0.0-1.0 — calibrated churn probability",
        "score_band": "LOW | MEDIUM-LOW | MEDIUM-HIGH | HIGH",
        "prediction": "0=NO_CHURN, 1=CHURN",
        "prediction_label": "NO_CHURN | CHURN",
        "threshold_used": "Decision boundary used",
        "score_meaning": "Calibrated probability of customer churn in next billing cycle",
        "model_version": "Semantic version of scoring model",
        "model_hash": "MD5 hash of model artifact",
        "scored_at": "UTC timestamp of scoring"
    },
    "score_bands": {"LOW": "<0.20", "MEDIUM-LOW": "0.20-0.40", "MEDIUM-HIGH": "0.40-0.60", "HIGH": ">=0.60"},
    "model_metadata": meta
}
with open('results/interface_documentation.json','w') as f:
    json.dump(interface_doc, f, indent=2)
print("  Saved: results/interface_documentation.json")

print("\n"+"="*65)
print("  PIPELINE COMPLETE")
print("  → python predict.py          (CLI live demo)")
print("  → python scoring/api.py      (start FastAPI server)")
print("="*65)
