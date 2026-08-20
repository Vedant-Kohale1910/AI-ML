import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score,
                             roc_auc_score, average_precision_score, confusion_matrix,
                             ConfusionMatrixDisplay, brier_score_loss)
from sklearn.model_selection import StratifiedKFold, cross_validate
import json

COST_FP = 5
COST_FN = 50


def compute_metrics(y_true, y_pred, y_prob, threshold=0.5):
    cm = confusion_matrix(y_true, y_pred)
    tn, fp, fn, tp = cm.ravel()
    cost = int(fp * COST_FP + fn * COST_FN)
    return {
        'accuracy': round(accuracy_score(y_true, y_pred), 4),
        'precision': round(precision_score(y_true, y_pred, zero_division=0), 4),
        'recall': round(recall_score(y_true, y_pred, zero_division=0), 4),
        'f1': round(f1_score(y_true, y_pred, zero_division=0), 4),
        'roc_auc': round(roc_auc_score(y_true, y_prob), 4),
        'pr_auc': round(average_precision_score(y_true, y_prob), 4),
        'brier_score': round(brier_score_loss(y_true, y_prob), 4),
        'tp': int(tp), 'tn': int(tn), 'fp': int(fp), 'fn': int(fn),
        'fpr': round(fp/(fp+tn+1e-9), 4), 'fnr': round(fn/(fn+tp+1e-9), 4),
        'expected_cost': cost, 'threshold': threshold
    }


def cross_val_stability(model, X, y, cv=5):
    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)
    scoring = {'f1':'f1','roc_auc':'roc_auc','precision':'precision','recall':'recall'}
    res = cross_validate(model, X, y, cv=skf, scoring=scoring, return_train_score=False)
    report = {}
    print(f"\n[CV] {cv}-Fold Cross-Validation Stability:")
    print(f"  {'Metric':<12} {'Mean':>8} {'Std':>8}")
    print(f"  {'-'*30}")
    for metric in ['f1','roc_auc','precision','recall']:
        vals = res[f'test_{metric}']
        report[metric] = {'mean': round(vals.mean(), 4), 'std': round(vals.std(), 4)}
        print(f"  {metric:<12} {vals.mean():>8.4f} {vals.std():>8.4f}")
    return report


def segment_evaluation(model, df_full, X_test_orig, y_test, threshold, scaler, feature_cols):
    """Evaluate performance per segment on test set."""
    from src.preprocess import SEGMENT_COLS
    results = []
    prob = model.predict_proba(X_test_orig)[:, 1]
    pred = (prob >= threshold).astype(int)
    # Reconstruct segment labels from scaled data using original indices
    # We'll pass the original df subset for test
    for seg_col, label_map in SEGMENT_COLS.items():
        if seg_col not in X_test_orig.columns:
            continue
        seg_vals = X_test_orig[seg_col].values
        for val, name in label_map.items():
            mask = (seg_vals == X_test_orig[seg_col].unique()[0]) if False else None
            # Use scaled value approximation: find rows where scaled col is closest
            # Simpler: re-index from X_test which has scaled values
            # We'll use original index reconstruction directly from test scaler inverse
            scaled_vals = X_test_orig[seg_col].values
            unique_scaled = sorted(X_test_orig[seg_col].unique())
            # Map to original: rank order preserved
            val_idx = sorted(label_map.keys()).index(val) if val in label_map else None
            if val_idx is None or val_idx >= len(unique_scaled):
                continue
            target_scaled = unique_scaled[val_idx]
            mask = np.abs(scaled_vals - target_scaled) < 0.01
            if mask.sum() < 10:
                continue
            yt = y_test.values[mask]
            yp = pred[mask]
            ypr = prob[mask]
            if len(np.unique(yt)) < 2:
                continue
            results.append({
                'segment': seg_col, 'group': name, 'n': int(mask.sum()),
                'precision': round(precision_score(yt, yp, zero_division=0), 4),
                'recall': round(recall_score(yt, yp, zero_division=0), 4),
                'f1': round(f1_score(yt, yp, zero_division=0), 4),
                'roc_auc': round(roc_auc_score(yt, ypr), 4)
            })
    return pd.DataFrame(results)


def plot_confusion_matrix(y_true, y_pred, path):
    fig, ax = plt.subplots(figsize=(5, 4))
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(cm, display_labels=['No Churn', 'Churn'])
    disp.plot(ax=ax, colorbar=False, cmap='Blues')
    ax.set_title('Confusion Matrix (Test Set)')
    plt.tight_layout()
    plt.savefig(path, dpi=100); plt.close()


def plot_segment_f1(seg_df, path):
    if seg_df.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 4))
    colors = ['steelblue' if f >= 0.70 else 'tomato' for f in seg_df['f1']]
    bars = ax.barh(seg_df['group'] + ' (' + seg_df['segment'] + ')', seg_df['f1'], color=colors)
    for bar, val in zip(bars, seg_df['f1']):
        ax.text(bar.get_width()+0.005, bar.get_y()+bar.get_height()/2, f'{val:.3f}', va='center', fontsize=8)
    ax.set_xlabel('F1 Score'); ax.set_title('Segment F1 Scores (red = below 0.70 threshold)')
    ax.axvline(0.70, color='red', linestyle='--', alpha=0.5)
    ax.set_xlim(0, 1.05)
    plt.tight_layout(); plt.savefig(path, dpi=100); plt.close()


def document_operating_point(metrics, threshold, path):
    doc = {
        'operating_point': {
            'threshold': threshold,
            'justification': f'Cost-optimal: minimises FP×₹{COST_FP} + FN×₹{COST_FN}',
            'precision': metrics['precision'],
            'recall': metrics['recall'],
            'f1': metrics['f1'],
            'roc_auc': metrics['roc_auc'],
            'false_positive_rate': metrics['fpr'],
            'false_negative_rate': metrics['fnr'],
            'true_positives': metrics['tp'],
            'false_positives': metrics['fp'],
            'false_negatives': metrics['fn'],
            'expected_total_cost': f"₹{metrics['expected_cost']}",
            'brier_score': metrics['brier_score'],
            'pr_auc': metrics['pr_auc'],
        }
    }
    with open(path, 'w') as f:
        json.dump(doc, f, indent=2)
    print(f"\n[Operating Point]")
    for k, v in doc['operating_point'].items():
        print(f"  {k:<28}: {v}")
    return doc
