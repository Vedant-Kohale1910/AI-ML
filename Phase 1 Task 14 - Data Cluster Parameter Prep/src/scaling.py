"""Feature scaling: demonstrate unscaled vs scaled distance dominance + apply StandardScaler."""
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib
from sklearn.preprocessing import StandardScaler


def demonstrate_scaling_effect(df: pd.DataFrame, features: list, plot_path: str = None):
    """Show how unscaled features distort distances."""
    ranges_unscaled = df[features].max() - df[features].min()
    print("\n[Scaling] Feature ranges BEFORE scaling (unscaled):")
    for f, r in ranges_unscaled.items():
        dominant = " ← would dominate" if r == ranges_unscaled.max() else ""
        print(f"  {f:<22}: range = {r:>12.2f}{dominant}")

    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(df[features]), columns=features)
    ranges_scaled = X_scaled.max() - X_scaled.min()
    print("\n[Scaling] Feature ranges AFTER StandardScaler:")
    for f, r in ranges_scaled.items():
        print(f"  {f:<22}: range = {r:>8.4f}  (mean≈0, std≈1)")

    if plot_path:
        fig, axes = plt.subplots(2, len(features), figsize=(16, 8))
        for i, f in enumerate(features):
            axes[0, i].hist(df[f], bins=30, color='#e74c3c', alpha=0.8, edgecolor='white')
            axes[0, i].set_title(f'{f}\n(unscaled)', fontsize=8)
            axes[0, i].set_xlabel(f'range: {ranges_unscaled[f]:.0f}', fontsize=7)
            axes[1, i].hist(X_scaled[f], bins=30, color='#27ae60', alpha=0.8, edgecolor='white')
            axes[1, i].set_title(f'{f}\n(scaled)', fontsize=8)
            axes[1, i].set_xlabel(f'range: {ranges_scaled[f]:.2f}', fontsize=7)
        axes[0, 0].set_ylabel('Unscaled')
        axes[1, 0].set_ylabel('StandardScaled')
        plt.suptitle('Feature Distributions: Before vs After Scaling', fontsize=12)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=100); plt.close()
        print(f"  Plot saved: {plot_path}")

    return X_scaled, scaler


def scale_features(df: pd.DataFrame, features: list, scaler=None):
    if scaler is None:
        scaler = StandardScaler()
        X_scaled = pd.DataFrame(scaler.fit_transform(df[features]), columns=features)
    else:
        X_scaled = pd.DataFrame(scaler.transform(df[features]), columns=features)
    return X_scaled, scaler
