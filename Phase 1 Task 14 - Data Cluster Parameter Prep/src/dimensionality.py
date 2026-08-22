"""PCA dimensionality reduction: variance explained + decision."""
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
import joblib


def pca_analysis(X_scaled: pd.DataFrame, plot_path: str = None, variance_threshold: float = 0.90):
    """Run PCA, plot variance explained, decide n_components."""
    n_features = X_scaled.shape[1]
    pca_full = PCA(n_components=n_features, random_state=42)
    pca_full.fit(X_scaled)
    cumvar = np.cumsum(pca_full.explained_variance_ratio_)

    n_components = int(np.argmax(cumvar >= variance_threshold) + 1)
    print(f"\n[PCA] Explained variance per component:")
    for i, (ev, cv) in enumerate(zip(pca_full.explained_variance_ratio_, cumvar)):
        marker = " ← chosen cutoff" if i + 1 == n_components else ""
        print(f"  PC{i+1}: {ev:.4f} ({cv:.4f} cumulative){marker}")
    print(f"  → {n_components} components explain {cumvar[n_components-1]:.1%} variance (≥{variance_threshold:.0%} threshold)")

    pca = PCA(n_components=n_components, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    X_pca_df = pd.DataFrame(X_pca, columns=[f'PC{i+1}' for i in range(n_components)])

    print(f"\n[PCA] Loadings (contribution of each feature per component):")
    loadings = pd.DataFrame(pca.components_.T, index=X_scaled.columns,
                             columns=[f'PC{i+1}' for i in range(n_components)])
    print(loadings.round(4).to_string())

    if plot_path:
        fig, axes = plt.subplots(1, 2, figsize=(12, 4))
        axes[0].bar(range(1, n_features+1), pca_full.explained_variance_ratio_, color='steelblue', alpha=0.8)
        axes[0].plot(range(1, n_features+1), cumvar, 'r-o', markersize=5, label='Cumulative')
        axes[0].axhline(variance_threshold, color='navy', linestyle='--', label=f'{variance_threshold:.0%} threshold')
        axes[0].axvline(n_components, color='green', linestyle='--', label=f'n={n_components}')
        axes[0].set_xlabel('Principal Component'); axes[0].set_ylabel('Variance Explained')
        axes[0].set_title('PCA Scree Plot'); axes[0].legend(fontsize=8); axes[0].grid(alpha=0.3)
        # PC1 vs PC2 scatter
        axes[1].scatter(X_pca_df['PC1'], X_pca_df['PC2'], alpha=0.3, s=10, c='steelblue')
        axes[1].set_xlabel('PC1'); axes[1].set_ylabel('PC2')
        axes[1].set_title('PCA: PC1 vs PC2 (all points)')
        plt.tight_layout(); plt.savefig(plot_path, dpi=100); plt.close()
        print(f"  Plot saved: {plot_path}")

    return X_pca_df, pca, n_components, loadings
