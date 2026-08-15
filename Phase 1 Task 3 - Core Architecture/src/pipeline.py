"""Assemble preprocessor + model into a single sklearn Pipeline."""
from sklearn.pipeline import Pipeline
from src.features.preprocessing import build_preprocessor
from src.models.model import create_model


def build_pipeline(X, model_name: str, model_params: dict, random_seed: int) -> Pipeline:
    preprocessor = build_preprocessor(X)
    model = create_model(model_name, model_params, random_seed)
    pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("model", model),
    ])
    print(f"  [Pipeline] Built: Preprocessor → {model_name}")
    return pipe
