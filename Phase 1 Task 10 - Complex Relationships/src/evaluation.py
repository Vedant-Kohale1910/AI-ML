from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import json


def compute_metrics(y_true, y_pred, y_prob):
    return {
        'accuracy': round(accuracy_score(y_true, y_pred), 4),
        'precision': round(precision_score(y_true, y_pred), 4),
        'recall': round(recall_score(y_true, y_pred), 4),
        'f1': round(f1_score(y_true, y_pred), 4),
        'roc_auc': round(roc_auc_score(y_true, y_prob), 4),
    }


def print_comparison(baseline_metrics, nonlinear_metrics, split='Test'):
    print(f"\n{'='*52}")
    print(f"TASK 10 RESULTS — {split} Set")
    print(f"{'='*52}")
    print(f"Baseline : Task 9 Tuned Random Forest")
    print(f"New Model: XGBoost (Non-linear)")
    print(f"\n{'Metric':<12} {'Baseline':>10} {'Non-linear':>12} {'Lift':>8}")
    print('-'*46)
    for k in baseline_metrics:
        b = baseline_metrics[k]
        n = nonlinear_metrics[k]
        lift = n - b
        print(f"{k:<12} {b:>10.4f} {n:>12.4f} {lift:>+8.4f}")
    print(f"{'='*52}\n")


def save_metrics(baseline, nonlinear, path):
    with open(path, 'w') as f:
        json.dump({'baseline': baseline, 'nonlinear': nonlinear}, f, indent=2)
