import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

# Business costs: losing a churned customer >> false alarm cost
COST_FP = 5    # Unnecessary retention offer (₹5)
COST_FN = 50   # Lost customer revenue (₹50)


def find_optimal_threshold(model, X_val, y_val, thresholds=None, plot_path=None):
    if thresholds is None:
        thresholds = np.arange(0.10, 0.91, 0.05)
    prob = model.predict_proba(X_val)[:, 1]
    records = []
    for t in thresholds:
        pred = (prob >= t).astype(int)
        cm = confusion_matrix(y_val, pred)
        tn, fp, fn, tp = cm.ravel() if cm.shape == (2,2) else (0,0,0,0)
        cost = fp * COST_FP + fn * COST_FN
        records.append({
            'threshold': round(t, 2), 'tp': int(tp), 'tn': int(tn),
            'fp': int(fp), 'fn': int(fn),
            'precision': round(precision_score(y_val, pred, zero_division=0), 4),
            'recall': round(recall_score(y_val, pred, zero_division=0), 4),
            'f1': round(f1_score(y_val, pred, zero_division=0), 4),
            'total_cost': int(cost)
        })
    df = pd.DataFrame(records)
    best_idx = df['total_cost'].idxmin()
    best = df.loc[best_idx]

    if plot_path:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        axes[0].plot(df['threshold'], df['total_cost'], 'r-o', markersize=4)
        axes[0].axvline(best['threshold'], color='navy', linestyle='--', label=f"Optimal={best['threshold']}")
        axes[0].set_xlabel('Threshold'); axes[0].set_ylabel('Total Cost (₹)')
        axes[0].set_title('Cost vs Threshold'); axes[0].legend(); axes[0].grid(alpha=0.3)
        axes[1].plot(df['threshold'], df['precision'], 'b-o', markersize=4, label='Precision')
        axes[1].plot(df['threshold'], df['recall'], 'g-o', markersize=4, label='Recall')
        axes[1].plot(df['threshold'], df['f1'], 'r-o', markersize=4, label='F1')
        axes[1].axvline(best['threshold'], color='navy', linestyle='--')
        axes[1].set_xlabel('Threshold'); axes[1].set_title('Metrics vs Threshold')
        axes[1].legend(); axes[1].grid(alpha=0.3)
        plt.suptitle(f'Threshold Analysis (FP cost=₹{COST_FP}, FN cost=₹{COST_FN})', fontsize=11)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=100); plt.close()
        print(f"[Threshold] Plot saved: {plot_path}")

    return df, float(best['threshold'])
