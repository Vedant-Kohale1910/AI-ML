"""Model factory — plug any sklearn estimator in via config."""
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier


REGISTRY = {
    "dummy": DummyClassifier,
    "logistic": LogisticRegression,
    "random_forest": RandomForestClassifier,
}


def create_model(name: str, params: dict = None, random_seed: int = 42):
    """
    Instantiate a model by name from the registry.

    To add a new model:
      1. Import the estimator above.
      2. Add it to REGISTRY with a string key.
      3. Set model.name + model.params in config/config.yaml.
      4. Run  python train.py  — no other changes needed.
    """
    params = params or {}
    if name not in REGISTRY:
        raise ValueError(f"Unknown model '{name}'. Available: {list(REGISTRY)}")
    # Inject random_state where the model supports it
    cls = REGISTRY[name]
    import inspect
    if "random_state" in inspect.signature(cls).parameters:
        params.setdefault("random_state", random_seed)
    model = cls(**params)
    print(f"  [ModelFactory] Created '{name}' → {model}")
    return model
