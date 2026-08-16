"""Train simple first models through the harness."""
import inspect
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.dummy import DummyClassifier

REGISTRY = {
    "logistic":      LogisticRegression,
    "decision_tree": DecisionTreeClassifier,
    "dummy":         DummyClassifier,
}

def train_model(name: str, X_train, y_train, seed=42, params=None):
    params = params or {}
    cls = REGISTRY[name]
    if "random_state" in inspect.signature(cls).parameters:
        params.setdefault("random_state", seed)
    model = cls(**params)
    model.fit(X_train, y_train)
    print(f"  [Train] '{name}' fitted on {X_train.shape[0]} rows")
    return model
