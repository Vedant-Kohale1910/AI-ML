import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import brier_score_loss


def calibrate(model, X_val, y_val, method='sigmoid'):
    cal = CalibratedClassifierCV(model, method=method, cv=5)
    cal.fit(X_val, y_val)
    return cal


def brier(model, X, y):
    prob = model.predict_proba(X)[:, 1]
    return round(brier_score_loss(y, prob), 4)


def plot_calibration_curve(models_dict, X_test, y_test, path):
    """Plot calibration curves for uncal and calibrated models."""
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
    colors = ['#E74C3C', '#2ECC71', '#3498DB', '#9B59B6']
    for (name, model), color in zip(models_dict.items(), colors):
        prob = model.predict_proba(X_test)[:, 1]
        frac_pos, mean_pred = calibration_curve(y_test, prob, n_bins=10)
        bs = brier_score_loss(y_test, prob)
        ax.plot(mean_pred, frac_pos, 'o-', color=color, label=f'{name} (Brier={bs:.4f})')
    ax.set_xlabel('Mean Predicted Probability')
    ax.set_ylabel('Fraction of Positives')
    ax.set_title('Calibration Curves')
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(path, dpi=100)
    plt.close()
    print(f"[Calibration] Curve saved: {path}")
