import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

FEATURE_COLS = ['tenure','monthly_charges','total_charges','num_products',
                'support_calls','contract_type','payment_method','age_group',
                'region','internet_service','online_backup','tech_support']
TARGET = 'churn'
RANDOM_STATE = 42
SEGMENT_COLS = {'age_group': {0:'18-25',1:'26-40',2:'41-60',3:'60+'},
                'region': {0:'North',1:'South',2:'East',3:'West'},
                'contract_type': {0:'Month-to-Month',1:'One Year',2:'Two Year'}}


def load_data(path):
    df = pd.read_csv(path)
    df['charges_per_tenure'] = df['monthly_charges'] / (df['tenure'] + 1)
    df['high_support'] = (df['support_calls'] > 3).astype(int)
    feats = FEATURE_COLS + ['charges_per_tenure', 'high_support']
    return df, df[feats], df[TARGET], feats


def split_scale(X, y):
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.3, random_state=RANDOM_STATE, stratify=y)
    X_val, X_te, y_val, y_te = train_test_split(X_tmp, y_tmp, test_size=0.5, random_state=RANDOM_STATE, stratify=y_tmp)
    sc = StandardScaler()
    cols = X.columns.tolist()
    X_tr_s = pd.DataFrame(sc.fit_transform(X_tr), columns=cols)
    X_val_s = pd.DataFrame(sc.transform(X_val), columns=cols)
    X_te_s = pd.DataFrame(sc.transform(X_te), columns=cols)
    return X_tr_s, X_val_s, X_te_s, y_tr.reset_index(drop=True), y_val.reset_index(drop=True), y_te.reset_index(drop=True), sc


def validate_input(data: dict, feature_cols: list) -> pd.DataFrame:
    if not data:
        raise ValueError("Input is empty.")
    missing = [f for f in feature_cols if f not in data]
    if missing:
        raise ValueError(f"Missing features: {missing}")
    row = {}
    for f in feature_cols:
        try:
            row[f] = float(data[f])
        except (TypeError, ValueError):
            raise ValueError(f"Feature '{f}' must be numeric, got: {data[f]}")
    return pd.DataFrame([row])
