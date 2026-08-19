from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
import pandas as pd
import time


def compute_metrics(y_true, y_pred, y_prob):
    return {
        'accuracy': round(accuracy_score(y_true, y_pred), 4),
        'precision': round(precision_score(y_true, y_pred, zero_division=0), 4),
        'recall': round(recall_score(y_true, y_pred, zero_division=0), 4),
        'f1': round(f1_score(y_true, y_pred, zero_division=0), 4),
        'roc_auc': round(roc_auc_score(y_true, y_prob), 4),
    }


def measure_latency(model, X_sample, n_runs=50):
    times = []
    for _ in range(n_runs):
        t0 = time.perf_counter()
        model.predict(X_sample)
        times.append((time.perf_counter() - t0) * 1000)
    return round(sum(times) / len(times), 3)


def print_results_table(results: dict):
    print(f"\n{'='*72}")
    print(f"{'Model':<25} {'Accuracy':>9} {'Precision':>10} {'Recall':>8} {'F1':>7} {'ROC-AUC':>9} {'Latency(ms)':>12}")
    print('-'*72)
    for name, m in results.items():
        print(f"{name:<25} {m['accuracy']:>9.4f} {m['precision']:>10.4f} {m['recall']:>8.4f} "
              f"{m['f1']:>7.4f} {m['roc_auc']:>9.4f} {m.get('latency_ms', '-'):>12}")
    print(f"{'='*72}\n")


def save_comparison(results: dict, path: str):
    rows = [{'model': k, **v} for k, v in results.items()]
    pd.DataFrame(rows).to_csv(path, index=False)
