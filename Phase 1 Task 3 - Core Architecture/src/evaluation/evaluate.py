"""Single evaluation module — all metric logic lives here."""
import csv, os
from datetime import datetime
from sklearn.metrics import (accuracy_score, precision_score,
                              recall_score, f1_score, classification_report)


def evaluate(model, X, y, split_name: str = "val") -> dict:
    y_pred = model.predict(X)
    metrics = {
        "split": split_name,
        "accuracy":  round(accuracy_score(y, y_pred), 4),
        "precision": round(precision_score(y, y_pred, zero_division=0, average="macro"), 4),
        "recall":    round(recall_score(y, y_pred, zero_division=0, average="macro"), 4),
        "f1_macro":  round(f1_score(y, y_pred, zero_division=0, average="macro"), 4),
    }
    print(f"\n  [Evaluator] {split_name.upper()} metrics:")
    for k, v in metrics.items():
        if k != "split":
            print(f"    {k:12s}: {v}")
    print("\n" + classification_report(y, y_pred,
          target_names=["Not Fraud", "Fraud"], zero_division=0))
    return metrics


def log_metrics(model_name: str, metrics: dict, config: dict,
                log_path: str = "experiments/metrics.csv") -> None:
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    exists = os.path.isfile(log_path)
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": model_name,
        **{k: v for k, v in metrics.items() if k != "split"},
        "split": metrics.get("split", "val"),
        "config_snapshot": str(config),
    }
    with open(log_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)
    print(f"  [Logger] Metrics logged → {log_path}")
