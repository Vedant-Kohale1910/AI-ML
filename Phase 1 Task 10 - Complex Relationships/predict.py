"""
Task 10 — Live Demo: predict.py
Loads the final model and predicts on real applicant samples.
Usage: python predict.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import numpy as np
import joblib
import json
from src.features import engineer_features

ARTIFACT_DIR = 'artifacts'

# Load artifacts
model = joblib.load(f'{ARTIFACT_DIR}/final_model.joblib')
scaler = joblib.load(f'{ARTIFACT_DIR}/scaler.joblib')
with open(f'{ARTIFACT_DIR}/feature_cols.json') as f:
    feature_cols = json.load(f)

# --- Real applicant samples from the dataset ---
sample_applicants = [
    {
        'name': 'Applicant A (Low Risk)',
        'credit_score': 780, 'monthly_income': 7500,
        'loan_amount': 10000, 'debt_to_income_ratio': 0.15,
        'employment_stability': 8, 'late_payment_rate': 0.02,
        'total_debt_burden': 1125.0
    },
    {
        'name': 'Applicant B (High Risk)',
        'credit_score': 420, 'monthly_income': 2000,
        'loan_amount': 35000, 'debt_to_income_ratio': 0.85,
        'employment_stability': 1, 'late_payment_rate': 0.45,
        'total_debt_burden': 1700.0
    },
    {
        'name': 'Applicant C (Moderate Risk)',
        'credit_score': 610, 'monthly_income': 4000,
        'loan_amount': 15000, 'debt_to_income_ratio': 0.40,
        'employment_stability': 4, 'late_payment_rate': 0.12,
        'total_debt_burden': 1600.0
    },
]

print("\n" + "="*60)
print("  TASK 10 — LIVE DEMO: Loan Default Prediction (XGBoost)")
print("="*60)

for app in sample_applicants:
    name = app.pop('name')
    df = pd.DataFrame([app])
    df = engineer_features(df)
    X = df[feature_cols]
    X_scaled = pd.DataFrame(scaler.transform(X), columns=feature_cols)
    pred = model.predict(X_scaled)[0]
    prob = model.predict_proba(X_scaled)[0][1]
    label = "⚠ DEFAULT" if pred == 1 else "✓ NO DEFAULT"
    print(f"\n  {name}")
    print(f"  Credit Score: {app.get('credit_score', '-')} | "
          f"DTI: {app.get('debt_to_income_ratio', '-')} | "
          f"Late Pmt Rate: {app.get('late_payment_rate', '-')}")
    print(f"  → Prediction : {label}")
    print(f"  → Probability: {prob:.2%}")

print("\n" + "="*60)
print("  Live demo complete. Model loaded from artifacts/final_model.joblib")
print("="*60 + "\n")
