import pandas as pd
import numpy as np

FEATURE_COLS = [
    'credit_score', 'monthly_income', 'loan_amount',
    'debt_to_income_ratio', 'employment_stability',
    'late_payment_rate', 'total_debt_burden'
]
TARGET_COL = 'default'


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['income_to_loan_ratio'] = df['monthly_income'] / (df['loan_amount'] + 1)
    df['credit_risk_flag'] = (df['credit_score'] < 600).astype(int)
    df['high_late_payment'] = (df['late_payment_rate'] > 0.2).astype(int)
    return df


def get_feature_cols(df: pd.DataFrame):
    base = FEATURE_COLS.copy()
    extras = ['income_to_loan_ratio', 'credit_risk_flag', 'high_late_payment']
    return [c for c in base + extras if c in df.columns]
