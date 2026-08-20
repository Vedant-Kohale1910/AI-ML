"""
Task 12 — Live Demo: predict.py
Loads calibrated model + optimal threshold, scores real customers with edge-case handling.
"""
import sys, os, json, warnings
sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings('ignore')
import joblib, pandas as pd
from src.preprocess import validate_input

MODEL_DIR = 'models'
model = joblib.load(f'{MODEL_DIR}/calibrated_model.joblib')
scaler = joblib.load(f'{MODEL_DIR}/scaler.joblib')
with open(f'{MODEL_DIR}/feature_cols.json') as f: feature_cols = json.load(f)
with open(f'{MODEL_DIR}/threshold.json') as f: threshold = json.load(f)['threshold']


def predict_customer(data: dict):
    try:
        X = validate_input(data, feature_cols)
        X_sc = pd.DataFrame(scaler.transform(X), columns=feature_cols)
        prob = float(model.predict_proba(X_sc)[0][1])
        pred = int(prob >= threshold)
        return {
            'calibrated_probability': round(prob, 4),
            'threshold_used': threshold,
            'prediction': pred,
            'label': '⚠ CHURN RISK' if pred == 1 else '✓ LIKELY TO STAY',
            'confidence': 'High' if abs(prob - 0.5) > 0.3 else 'Moderate' if abs(prob - 0.5) > 0.15 else 'Low'
        }
    except ValueError as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': f'Unexpected error: {e}'}


CUSTOMERS = [
    ('Customer A — Low Churn Risk', {
        'tenure':60,'monthly_charges':45.0,'total_charges':2700.0,'num_products':4,
        'support_calls':0,'contract_type':2,'payment_method':1,'age_group':2,
        'region':0,'internet_service':1,'online_backup':1,'tech_support':1,
        'charges_per_tenure':0.75,'high_support':0
    }),
    ('Customer B — High Churn Risk', {
        'tenure':3,'monthly_charges':105.0,'total_charges':315.0,'num_products':1,
        'support_calls':6,'contract_type':0,'payment_method':3,'age_group':0,
        'region':2,'internet_service':2,'online_backup':0,'tech_support':0,
        'charges_per_tenure':26.25,'high_support':1
    }),
    ('Customer C — Borderline', {
        'tenure':18,'monthly_charges':70.0,'total_charges':1260.0,'num_products':2,
        'support_calls':2,'contract_type':1,'payment_method':2,'age_group':1,
        'region':1,'internet_service':1,'online_backup':0,'tech_support':1,
        'charges_per_tenure':3.72,'high_support':0
    }),
]

EDGE_CASES = [
    ('Edge: Missing features', {'tenure': 12, 'monthly_charges': 60}),
    ('Edge: Invalid type', dict(tenure='abc', monthly_charges=60.0, total_charges=720.0,
        num_products=2, support_calls=1, contract_type=1, payment_method=0,
        age_group=1, region=0, internet_service=1, online_backup=1, tech_support=0,
        charges_per_tenure=5.0, high_support=0)),
    ('Edge: Empty input', {}),
]

print("\n" + "="*65)
print(f"  TASK 12 — LIVE DEMO: Calibrated Churn Classifier")
print(f"  Threshold: {threshold} | Costs: FP=₹5, FN=₹50")
print("="*65)

print("\n── Real Customer Predictions ──")
for name, data in CUSTOMERS:
    res = predict_customer(data)
    print(f"\n  {name}")
    if 'error' in res:
        print(f"  → ERROR: {res['error']}")
    else:
        print(f"  Tenure={data['tenure']}mo | Monthly=₹{data['monthly_charges']} | Calls={data['support_calls']} | Contract={data['contract_type']}")
        print(f"  → Calibrated Probability : {res['calibrated_probability']:.2%}")
        print(f"  → Threshold              : {res['threshold_used']}")
        print(f"  → Prediction             : {res['label']}")
        print(f"  → Confidence             : {res['confidence']}")

print("\n── Edge Case Handling ──")
for name, data in EDGE_CASES:
    res = predict_customer(data)
    print(f"\n  {name}")
    if 'error' in res:
        print(f"  → Handled: {str(res['error'])[:100]}")
    else:
        print(f"  → {res['label']} ({res['calibrated_probability']:.2%})")

print("\n" + "="*65)
print(f"  Demo complete. Model: {MODEL_DIR}/calibrated_model.joblib")
print("="*65 + "\n")
