"""Evaluation gate — pipeline reports metrics, not just predictions."""
import csv, json, os
from datetime import datetime
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, roc_auc_score, classification_report)


def compute_metrics(pipeline, X, y, split_name="val", model_name="model") -> dict:
    y_pred = pipeline.predict(X)
    y_prob = pipeline.predict_proba(X)[:, 1]
    m = {
        "split": split_name, "model": model_name,
        "accuracy":  round(accuracy_score(y, y_pred), 4),
        "precision": round(precision_score(y, y_pred, zero_division=0, average="macro"), 4),
        "recall":    round(recall_score(y, y_pred, zero_division=0, average="macro"), 4),
        "f1_macro":  round(f1_score(y, y_pred, zero_division=0, average="macro"), 4),
        "roc_auc":   round(roc_auc_score(y, y_prob), 4),
    }
    print(f"\n  [{split_name.upper()}] acc={m['accuracy']} prec={m['precision']} "
          f"rec={m['recall']} f1={m['f1_macro']} roc_auc={m['roc_auc']}")
    print(classification_report(y, y_pred, target_names=["No Default","Default"], zero_division=0))
    return m


def save_metrics(metrics: dict, path="artifacts/metrics.json") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"  [Artifacts] metrics.json saved → {path}")


def log_experiment(record: dict, path="artifacts/experiment_log.csv") -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    exists = os.path.isfile(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(record.keys()))
        if not exists: w.writeheader()
        w.writerow(record)
    print(f"  [Artifacts] experiment_log.csv updated → {path}")
