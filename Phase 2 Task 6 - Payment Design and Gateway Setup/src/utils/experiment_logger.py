"""
experiment_logger.py
--------------------
Thin wrapper around MLflow so the rest of the codebase doesn't have to
care about MLflow internals. If MLflow isn't available or errors out,
we fall back to a plain JSON log — the numbers always get recorded somewhere.
"""

import json
import os
import time
from typing import Any, Dict, Optional

try:
    import mlflow
    _MLFLOW_AVAILABLE = True
except ImportError:
    _MLFLOW_AVAILABLE = False


EXPERIMENT_DIR = os.path.join(os.path.dirname(__file__), "../../experiments")
FALLBACK_LOG = os.path.join(EXPERIMENT_DIR, "run_log.jsonl")


def _ensure_dirs():
    os.makedirs(EXPERIMENT_DIR, exist_ok=True)


def start_run(run_name: str, experiment_name: str = "placemux_matching"):
    _ensure_dirs()
    if _MLFLOW_AVAILABLE:
        mlflow.set_tracking_uri(f"file://{os.path.abspath(EXPERIMENT_DIR)}/mlruns")
        mlflow.set_experiment(experiment_name)
        mlflow.start_run(run_name=run_name)


def log_params(params: Dict[str, Any]):
    if _MLFLOW_AVAILABLE:
        try:
            mlflow.log_params(params)
            return
        except Exception:
            pass
    # fallback: just print
    for k, v in params.items():
        print(f"  [param] {k} = {v}")


def log_metrics(metrics: Dict[str, float], step: Optional[int] = None):
    if _MLFLOW_AVAILABLE:
        try:
            mlflow.log_metrics(metrics, step=step)
        except Exception:
            pass

    # always write to the fallback JSON log as well
    _ensure_dirs()
    record = {"timestamp": time.time(), "metrics": metrics}
    if step is not None:
        record["step"] = step
    with open(FALLBACK_LOG, "a") as f:
        f.write(json.dumps(record) + "\n")


def log_artifact(path: str):
    if _MLFLOW_AVAILABLE:
        try:
            mlflow.log_artifact(path)
        except Exception:
            pass


def end_run():
    if _MLFLOW_AVAILABLE:
        try:
            mlflow.end_run()
        except Exception:
            pass
