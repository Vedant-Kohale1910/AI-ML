"""Model training — Logistic Regression and Random Forest."""
import joblib, os, inspect
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

REGISTRY = {
    "logistic":      LogisticRegression,
    "random_forest": RandomForestClassifier,
}

def train_model(name, X_train, y_train, seed=42, params=None):
    params = params or {}
    cls = REGISTRY[name]
    if "random_state" in inspect.signature(cls).parameters:
        params.setdefault("random_state", seed)
    model = cls(**params)
    model.fit(X_train, y_train)
    print(f"  [Train] '{name}' fitted on {X_train.shape[0]} rows, {X_train.shape[1]} features")
    return model

def save_model(model, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(model, path)
    print(f"  [Save] Model → {path}")

def load_model(path):
    return joblib.load(path)
