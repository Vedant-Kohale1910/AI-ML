"""Evaluation and error analysis."""
import csv, os
import numpy as np
import pandas as pd
from datetime import datetime
from sklearn.metrics import (accuracy_score, precision_score, recall_score,
                              f1_score, classification_report, confusion_matrix)


def evaluate(model, X, y, split_name="val", model_name="model"):
    y_pred = model.predict(X)
    m = {
        "model":     model_name,
        "split":     split_name,
        "accuracy":  round(accuracy_score(y, y_pred), 4),
        "precision": round(precision_score(y, y_pred, zero_division=0, average="macro"), 4),
        "recall":    round(recall_score(y, y_pred, zero_division=0, average="macro"), 4),
        "f1_macro":  round(f1_score(y, y_pred, zero_division=0, average="macro"), 4),
    }
    print(f"\n  [{split_name.upper()}] {model_name}: "
          f"acc={m['accuracy']} prec={m['precision']} rec={m['recall']} f1={m['f1_macro']}")
    print(classification_report(y, y_pred, target_names=["Not Fraud","Fraud"], zero_division=0))
    return m, y_pred


def error_analysis(X_val_raw: pd.DataFrame, y_val, y_pred,
                   out_path="results/error_analysis.csv"):
    df = X_val_raw.copy()
    df["actual"]    = y_val.values
    df["predicted"] = y_pred
    df["correct"]   = (df["actual"] == df["predicted"]).astype(int)
    errors = df[df["correct"] == 0].copy()

    # Patterns
    print(f"\n  [ErrorAnalysis] Total val errors: {len(errors)} / {len(df)}")
    print(f"  Error breakdown by actual class:")
    print(errors["actual"].value_counts().to_string())
    print(f"\n  Numeric feature means — errors vs correct:")
    num_cols = X_val_raw.select_dtypes(include="number").columns
    comparison = pd.DataFrame({
        "errors_mean":  errors[num_cols].mean().round(2),
        "correct_mean": df[df["correct"]==1][num_cols].mean().round(2),
    })
    print(comparison.to_string())

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    errors.to_csv(out_path, index=False)
    print(f"\n  [ErrorAnalysis] Saved {len(errors)} error rows → {out_path}")
    return errors


def log_experiment(record: dict, path="experiment_log/experiment_log.csv"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    exists = os.path.isfile(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(record.keys()))
        if not exists: w.writeheader()
        w.writerow(record)
    print(f"  [ExpLog] → {path}")
