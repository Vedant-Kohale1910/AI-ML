"""Train and save the churn model with versioning metadata."""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, joblib, json, hashlib
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.calibration import CalibratedClassifierCV
from xgboost import XGBClassifier

RANDOM_STATE = 42
MODEL_VERSION = "v1.0.0"
FEATURE_COLS = ['tenure','monthly_charges','total_charges','num_products','support_calls',
                'contract_type','payment_method','age_group','region',
                'internet_service','online_backup','tech_support',
                'charges_per_tenure','high_support']
TARGET = 'churn'
THRESHOLD = 0.35
COST_FP, COST_FN = 5, 50


def load_and_prepare(path):
    df = pd.read_csv(path)
    df['charges_per_tenure'] = df['monthly_charges'] / (df['tenure'] + 1)
    df['high_support'] = (df['support_calls'] > 3).astype(int)
    X = df[FEATURE_COLS]; y = df[TARGET]
    return X, y


def train_and_save(data_path='data/churn_data.csv', model_dir='models'):
    print(f"[Train] Loading data from {data_path}...")
    X, y = load_and_prepare(data_path)

    X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=0.3, random_state=RANDOM_STATE, stratify=y)
    X_val, X_te, y_val, y_te = train_test_split(X_tmp, y_tmp, test_size=0.5, random_state=RANDOM_STATE, stratify=y_tmp)

    scaler = StandardScaler()
    X_tr_s = pd.DataFrame(scaler.fit_transform(X_tr), columns=FEATURE_COLS)
    X_val_s = pd.DataFrame(scaler.transform(X_val), columns=FEATURE_COLS)
    X_te_s = pd.DataFrame(scaler.transform(X_te), columns=FEATURE_COLS)

    print("[Train] Training XGBoost classifier...")
    xgb = XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05,
                        subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1, reg_lambda=1.0,
                        random_state=RANDOM_STATE, eval_metric='logloss', use_label_encoder=False)
    xgb.fit(X_tr_s, y_tr)

    print("[Train] Calibrating probabilities (isotonic)...")
    cal_model = CalibratedClassifierCV(xgb, method='isotonic', cv=5)
    cal_model.fit(X_tr_s, y_tr)

    # Evaluate
    from sklearn.metrics import roc_auc_score, f1_score
    prob_te = cal_model.predict_proba(X_te_s)[:, 1]
    pred_te = (prob_te >= THRESHOLD).astype(int)
    auc = roc_auc_score(y_te, prob_te)
    f1 = f1_score(y_te, pred_te)
    print(f"[Train] Test ROC-AUC={auc:.4f} | F1@{THRESHOLD}={f1:.4f}")

    # Compute model hash for integrity
    import io, pickle; buf = io.BytesIO(); pickle.dump(cal_model, buf)
    model_hash = hashlib.md5(buf.getvalue()).hexdigest()[:8]

    # Save artifacts
    joblib.dump(cal_model, f'{model_dir}/churn_model.joblib')
    joblib.dump(scaler, f'{model_dir}/scaler.joblib')

    metadata = {
        'model_version': MODEL_VERSION,
        'model_hash': model_hash,
        'trained_at': datetime.utcnow().isoformat() + 'Z',
        'algorithm': 'XGBoost + Isotonic Calibration',
        'feature_cols': FEATURE_COLS,
        'target': TARGET,
        'threshold': THRESHOLD,
        'score_semantics': 'Calibrated probability of customer churn (0.0–1.0)',
        'cost_fp': COST_FP,
        'cost_fn': COST_FN,
        'test_roc_auc': round(auc, 4),
        'test_f1': round(f1, 4),
        'training_rows': len(X_tr),
        'data_source': data_path,
    }
    with open(f'{model_dir}/model_metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"[Train] Saved: {model_dir}/churn_model.joblib")
    print(f"[Train] Model version: {MODEL_VERSION} | Hash: {model_hash}")
    return cal_model, scaler, metadata


if __name__ == '__main__':
    train_and_save()
