"""
Task 11 — Live Demo: predict.py
Loads the final stacking ensemble and predicts on real applicants.
Usage: python predict.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import warnings; warnings.filterwarnings('ignore')
import joblib, json
import pandas as pd
from src.preprocess import validate_input

ARTIFACT_DIR = 'models'

# Load
model = joblib.load(f'{ARTIFACT_DIR}/final_ensemble.joblib')
scaler = joblib.load(f'{ARTIFACT_DIR}/scaler.joblib')
with open(f'{ARTIFACT_DIR}/feature_cols.json') as f:
    feature_cols = json.load(f)
with open(f'{ARTIFACT_DIR}/final_model_label.json') as f:
    label = json.load(f)['label']

def predict_applicant(data: dict):
    """Predict loan default with edge-case handling."""
    try:
        X = validate_input(data, feature_cols)
        X_scaled = pd.DataFrame(scaler.transform(X), columns=feature_cols)
        pred = model.predict(X_scaled)[0]
        prob = model.predict_proba(X_scaled)[0][1]
        return {'prediction': int(pred), 'probability': round(float(prob), 4),
                'label': '⚠ DEFAULT' if pred == 1 else '✓ NO DEFAULT'}
    except ValueError as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': f'Unexpected error: {e}'}

# ── Real applicant samples ──
SAMPLES = [
    ('Applicant A — Low Risk',
     {'age':42,'income':85000,'credit_score':780,'loan_amount':15000,'debt_to_income':0.12,
      'employment_years':12,'num_accounts':6,'late_payments':0,'savings':32000,
      'education_level':3,'income_to_loan':85000/15001,'credit_risk':0,'debt_stress':0.0}),
    ('Applicant B — High Risk',
     {'age':28,'income':22000,'credit_score':420,'loan_amount':55000,'debt_to_income':0.92,
      'employment_years':1,'num_accounts':2,'late_payments':5,'savings':800,
      'education_level':0,'income_to_loan':22000/55001,'credit_risk':1,'debt_stress':0.92*5}),
    ('Applicant C — Moderate Risk',
     {'age':35,'income':48000,'credit_score':620,'loan_amount':25000,'debt_to_income':0.40,
      'employment_years':5,'num_accounts':4,'late_payments':1,'savings':8000,
      'education_level':2,'income_to_loan':48000/25001,'credit_risk':0,'debt_stress':0.40*1}),
]

# ── Edge case samples ──
EDGE_CASES = [
    ('Edge Case: Missing feature', {'age': 35, 'income': 48000}),  # missing fields
    ('Edge Case: Invalid type', {'age': 'thirty', 'income': 48000, 'credit_score': 620,
      'loan_amount': 25000, 'debt_to_income': 0.4, 'employment_years': 5,
      'num_accounts': 4, 'late_payments': 1, 'savings': 8000, 'education_level': 2,
      'income_to_loan': 1.92, 'credit_risk': 0, 'debt_stress': 0.4}),
    ('Edge Case: Empty input', {}),
]

print("\n" + "="*62)
print(f"  TASK 11 — LIVE DEMO: {label}")
print("="*62)

print("\n── Real Applicant Predictions ──")
for name, data in SAMPLES:
    result = predict_applicant(data)
    if 'error' in result:
        print(f"\n  {name}\n  → ERROR: {result['error']}")
    else:
        print(f"\n  {name}")
        print(f"  Credit Score: {data['credit_score']} | DTI: {data['debt_to_income']} | Late Pmts: {data['late_payments']}")
        print(f"  → Prediction : {result['label']}")
        print(f"  → Probability: {result['probability']:.2%}")

print("\n── Edge Case Handling ──")
for name, data in EDGE_CASES:
    result = predict_applicant(data)
    print(f"\n  {name}")
    if 'error' in result:
        print(f"  → Handled gracefully: {result['error'][:80]}")
    else:
        print(f"  → {result['label']} ({result['probability']:.2%})")

print("\n" + "="*62)
print("  Live demo complete. Model: models/final_ensemble.joblib")
print("="*62 + "\n")
