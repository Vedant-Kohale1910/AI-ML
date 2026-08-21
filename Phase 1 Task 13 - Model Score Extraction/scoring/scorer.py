"""Core scoring engine: single-record and batch scoring with versioned output."""
import os, sys, json, joblib, warnings
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
warnings.filterwarnings('ignore')
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from scoring.schema import CustomerInput, ScoreOutput, BatchInput, BatchOutput, score_band

MODEL_DIR = 'models'
_model = None
_scaler = None
_metadata = None


def _load_artifacts():
    global _model, _scaler, _metadata
    if _model is None:
        _model = joblib.load(f'{MODEL_DIR}/churn_model.joblib')
        _scaler = joblib.load(f'{MODEL_DIR}/scaler.joblib')
        with open(f'{MODEL_DIR}/model_metadata.json') as f:
            _metadata = json.load(f)
    return _model, _scaler, _metadata


def _prepare_features(data: dict) -> pd.DataFrame:
    feat = {k: v for k, v in data.items()}
    feat['charges_per_tenure'] = feat['monthly_charges'] / (feat['tenure'] + 1)
    feat['high_support'] = int(feat['support_calls'] > 3)
    _, scaler, meta = _load_artifacts()
    cols = meta['feature_cols']
    X = pd.DataFrame([[feat[c] for c in cols]], columns=cols)
    return pd.DataFrame(scaler.transform(X), columns=cols)


def score_single(record: CustomerInput, record_id: str = None) -> ScoreOutput:
    model, _, meta = _load_artifacts()
    X = _prepare_features(record.dict())
    prob = float(model.predict_proba(X)[0][1])
    threshold = meta['threshold']
    pred = int(prob >= threshold)
    return ScoreOutput(
        record_id=record_id,
        score=round(prob, 6),
        score_band=score_band(prob),
        prediction=pred,
        prediction_label='CHURN' if pred == 1 else 'NO_CHURN',
        threshold_used=threshold,
        model_version=meta['model_version'],
        model_hash=meta['model_hash'],
        scored_at=datetime.now(timezone.utc).isoformat()
    )


def score_batch(batch: BatchInput) -> BatchOutput:
    model, scaler, meta = _load_artifacts()
    threshold = meta['threshold']
    cols = meta['feature_cols']
    scores, errors = [], []
    now = datetime.now(timezone.utc).isoformat()

    for i, record in enumerate(batch.records):
        rid = f"{batch.batch_id or 'batch'}-{i}"
        try:
            result = score_single(record, record_id=rid)
            scores.append(result.dict())
        except Exception as e:
            errors.append({'record_index': i, 'record_id': rid, 'error': str(e)})

    return BatchOutput(
        batch_id=batch.batch_id,
        total_records=len(batch.records),
        scored_records=len(scores),
        failed_records=len(errors),
        model_version=meta['model_version'],
        scores=scores,
        errors=errors,
        scored_at=now
    )


def score_csv(input_path: str, output_path: str):
    """Score a CSV file and write results."""
    model, scaler, meta = _load_artifacts()
    df = pd.read_csv(input_path)
    df['charges_per_tenure'] = df['monthly_charges'] / (df['tenure'] + 1)
    df['high_support'] = (df['support_calls'] > 3).astype(int)
    cols = meta['feature_cols']
    X = df[cols]
    X_s = pd.DataFrame(scaler.transform(X), columns=cols)
    prob = model.predict_proba(X_s)[:, 1]
    threshold = meta['threshold']
    df['churn_score'] = prob.round(6)
    df['score_band'] = [score_band(p) for p in prob]
    df['prediction'] = (prob >= threshold).astype(int)
    df['prediction_label'] = df['prediction'].map({0:'NO_CHURN', 1:'CHURN'})
    df['model_version'] = meta['model_version']
    df['model_hash'] = meta['model_hash']
    df['scored_at'] = datetime.now(timezone.utc).isoformat()
    df.to_csv(output_path, index=False)
    print(f"[Batch CSV] Scored {len(df)} records → {output_path}")
    print(f"  Churn predicted: {df['prediction'].sum()} ({df['prediction'].mean():.2%})")
    return df
