import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

FEATURE_COLS = ['age','income','credit_score','loan_amount','debt_to_income',
                'employment_years','num_accounts','late_payments','savings','education_level']
TARGET = 'default'
RANDOM_STATE = 42


def load_data(path: str):
    df = pd.read_csv(path)
    # Feature engineering
    df['income_to_loan'] = df['income'] / (df['loan_amount'] + 1)
    df['credit_risk'] = (df['credit_score'] < 600).astype(int)
    df['debt_stress'] = df['debt_to_income'] * df['late_payments']
    all_feats = FEATURE_COLS + ['income_to_loan', 'credit_risk', 'debt_stress']
    X = df[all_feats]
    y = df[TARGET]
    return X, y, all_feats


def split_and_scale(X, y):
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.3, random_state=RANDOM_STATE, stratify=y)
    X_val, X_te, y_val, y_te = train_test_split(X_tmp, y_tmp, test_size=0.5, random_state=RANDOM_STATE, stratify=y_tmp)
    scaler = StandardScaler()
    X_tr_s = pd.DataFrame(scaler.fit_transform(X_tr), columns=X.columns)
    X_val_s = pd.DataFrame(scaler.transform(X_val), columns=X.columns)
    X_te_s = pd.DataFrame(scaler.transform(X_te), columns=X.columns)
    return X_tr_s, X_val_s, X_te_s, y_tr.reset_index(drop=True), y_val.reset_index(drop=True), y_te.reset_index(drop=True), scaler


def validate_input(data: dict, feature_cols: list):
    """Edge-case handler for live inference."""
    errors = []
    if not data:
        raise ValueError("Input data is empty.")
    for col in feature_cols:
        if col not in data:
            errors.append(f"Missing feature: {col}")
    if errors:
        raise ValueError(f"Input errors: {errors}")
    row = {}
    for col in feature_cols:
        try:
            row[col] = float(data[col])
        except (TypeError, ValueError):
            raise ValueError(f"Feature '{col}' must be numeric, got: {data[col]}")
    return pd.DataFrame([row])
