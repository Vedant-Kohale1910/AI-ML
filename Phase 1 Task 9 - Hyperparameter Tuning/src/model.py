"""Model factory."""
import inspect
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

REGISTRY = {
    "random_forest": RandomForestClassifier,
    "logistic":      LogisticRegression,
}

def create_model(name="random_forest", params=None, seed=42):
    params = params or {}
    cls = REGISTRY[name]
    if "random_state" in inspect.signature(cls).parameters:
        params.setdefault("random_state", seed)
    if name == "random_forest":
        params.setdefault("n_estimators", 100)
        params.setdefault("class_weight", "balanced")
    if name == "logistic":
        params.setdefault("max_iter", 1000)
        params.setdefault("class_weight", "balanced")
    return cls(**params)
