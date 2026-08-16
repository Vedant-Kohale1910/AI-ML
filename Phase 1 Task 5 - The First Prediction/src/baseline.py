"""Baseline — majority-class classifier."""
import numpy as np
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score


def compute_baseline(y_train, y_val):
    majority = int(y_train.value_counts().idxmax())
    y_pred = np.full(len(y_val), majority)
    metrics = {
        "model":     "MajorityClass_Baseline",
        "accuracy":  round(accuracy_score(y_val, y_pred), 4),
        "precision": round(precision_score(y_val, y_pred, zero_division=0, average="macro"), 4),
        "recall":    round(recall_score(y_val, y_pred, zero_division=0, average="macro"), 4),
        "f1_macro":  round(f1_score(y_val, y_pred, zero_division=0, average="macro"), 4),
        "majority_class": majority,
    }
    print(f"  [Baseline] Always predict class {majority} → "
          f"acc={metrics['accuracy']} f1={metrics['f1_macro']}")
    return metrics, y_pred
