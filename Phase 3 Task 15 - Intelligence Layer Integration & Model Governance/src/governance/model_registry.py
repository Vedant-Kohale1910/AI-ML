"""
model_registry.py — Stage B
A file-backed model registry (JSON) storing every model version,
its metrics, training data lineage, and production status.

Why file-backed over MLflow?
  MLflow requires a running server (SQLite/PostgreSQL + tracking URI).
  For a self-contained demo that runs on Windows with no extra services,
  a JSON registry is functionally identical for audit purposes and is
  100% reproducible. The registry schema is MLflow-compatible so migration
  is one command: `mlflow models register`. Rejected: MLflow server
  (adds a service dependency that breaks the demo on first run).

Design: append-only. Old versions are NEVER deleted — only status changes.
"""
import json
import os
import time
import uuid

REGISTRY_PATH = os.path.join(os.path.dirname(__file__), "../../reports/model_registry.json")


def _load():
    if os.path.exists(REGISTRY_PATH):
        with open(REGISTRY_PATH) as f:
            return json.load(f)
    return {"models": []}


def _save(reg):
    os.makedirs(os.path.dirname(REGISTRY_PATH), exist_ok=True)
    with open(REGISTRY_PATH, "w") as f:
        json.dump(reg, f, indent=2)


def register_model(name: str, version: str, metrics: dict,
                   training_data: str, feature_names: list,
                   status: str = "staging") -> dict:
    """Register a new model version. Returns the registry entry."""
    reg = _load()
    # Retire any existing 'production' entry for same model name
    if status == "production":
        for m in reg["models"]:
            if m["name"] == name and m["status"] == "production":
                m["status"] = "archived"

    entry = {
        "run_id":        "RUN-" + uuid.uuid4().hex[:8].upper(),
        "name":          name,
        "version":       version,
        "status":        status,          # staging | production | archived | rolled_back
        "metrics":       metrics,
        "training_data": training_data,
        "feature_names": feature_names,
        "registered_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "lineage": {
            "source_data":   training_data,
            "pipeline":      "run_pipeline.py",
            "reproducible":  True,
        },
    }
    reg["models"].append(entry)
    _save(reg)
    return entry


def promote(name: str, version: str) -> dict:
    """Promote a staging model to production (with evaluation gate check)."""
    reg = _load()
    target = next((m for m in reg["models"]
                   if m["name"] == name and m["version"] == version), None)
    if not target:
        raise ValueError(f"Model {name} v{version} not found in registry")
    # Evaluation gate: new model must beat the current production model
    prod = next((m for m in reg["models"]
                 if m["name"] == name and m["status"] == "production"), None)
    if prod:
        new_ndcg = target["metrics"].get("ndcg_at_5", 0)
        old_ndcg = prod["metrics"].get("ndcg_at_5", 0)
        if new_ndcg < old_ndcg:
            raise ValueError(
                f"Evaluation gate FAILED: new nDCG@5={new_ndcg} ≤ current={old_ndcg}. "
                "Deployment blocked. Fix the model or lower the gate threshold.")
        prod["status"] = "archived"
    target["status"] = "production"
    _save(reg)
    return target


def rollback(name: str) -> dict:
    """Roll back: demote current production, promote most-recent archived."""
    reg = _load()
    prod = next((m for m in reg["models"]
                 if m["name"] == name and m["status"] == "production"), None)
    if prod:
        prod["status"] = "rolled_back"
    archived = [m for m in reg["models"]
                if m["name"] == name and m["status"] == "archived"]
    if not archived:
        raise ValueError(f"No archived version of {name} to roll back to")
    # Most recently registered archived version
    prev = sorted(archived, key=lambda x: x["registered_at"])[-1]
    prev["status"] = "production"
    _save(reg)
    return {"rolled_back_from": prod, "restored": prev}


def get_production(name: str) -> dict:
    reg = _load()
    return next((m for m in reg["models"]
                 if m["name"] == name and m["status"] == "production"), None)


def list_versions(name: str) -> list:
    reg = _load()
    return [m for m in reg["models"] if m["name"] == name]


def promote_force(name: str, version: str) -> dict:
    """Force-promote any version (e.g., for rollback demo). No eval gate."""
    reg = _load()
    target = next((m for m in reg["models"]
                   if m["name"] == name and m["version"] == version), None)
    if not target:
        raise ValueError(f"Model {name} v{version} not found in registry")
    for m in reg["models"]:
        if m["name"] == name and m["status"] == "production":
            m["status"] = "archived"
    target["status"] = "production"
    _save(reg)
    return target
