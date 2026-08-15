"""Model factory."""
import inspect
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier

REGISTRY = {
    "dummy":         DummyClassifier,
    "logistic":      LogisticRegression,
    "random_forest": RandomForestClassifier,
}

def create_model(name: str, params: dict = None, random_seed: int = 42):
    params = params or {}
    cls = REGISTRY[name]
    if "random_state" in inspect.signature(cls).parameters:
        params.setdefault("random_state", random_seed)
    model = cls(**params)
    print(f"  [Model] Created '{name}' → {model}")
    return model
