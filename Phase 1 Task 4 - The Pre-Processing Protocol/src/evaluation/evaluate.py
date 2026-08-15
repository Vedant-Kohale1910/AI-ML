"""Single evaluation module."""
import csv, os
from datetime import datetime
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report

def evaluate(model, X, y, split_name="val"):
    y_pred = model.predict(X)
    m = {
        "split":     split_name,
        "accuracy":  round(accuracy_score(y, y_pred), 4),
        "precision": round(precision_score(y, y_pred, zero_division=0, average="macro"), 4),
        "recall":    round(recall_score(y, y_pred, zero_division=0, average="macro"), 4),
        "f1_macro":  round(f1_score(y, y_pred, zero_division=0, average="macro"), 4),
    }
    print(f"\n  [{split_name.upper()}] acc={m['accuracy']} prec={m['precision']} rec={m['recall']} f1={m['f1_macro']}")
    print(classification_report(y, y_pred, target_names=["Not Fraud","Fraud"], zero_division=0))
    return m

def log_metrics(model_name, metrics, log_path):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    exists = os.path.isfile(log_path)
    row = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "model": model_name, **metrics}
    with open(log_path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists: w.writeheader()
        w.writerow(row)
    print(f"  [Logger] → {log_path}")
