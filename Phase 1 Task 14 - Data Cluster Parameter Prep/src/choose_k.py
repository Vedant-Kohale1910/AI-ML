"""Choose k: elbow method (inertia) + silhouette score + distance sanity check."""
import numpy as np
import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score, davies_bouldin_score
import json


def elbow_and_silhouette(X: pd.DataFrame, k_range=range(2, 11), random_state=42, plot_path=None):
    inertias, silhouettes, db_scores = [], [], []
    print(f"\n[Choose k] Testing k={list(k_range)}...")
    print(f"  {'k':>3} {'Inertia':>12} {'Silhouette':>12} {'Davies-Bouldin':>16}")
    print(f"  {'-'*46}")
    for k in k_range:
        km = KMeans(n_clusters=k, init='k-means++', n_init=10, max_iter=300, random_state=random_state)
        labels = km.fit_predict(X)
        inertias.append(km.inertia_)
        sil = silhouette_score(X, labels, sample_size=min(1000, len(X)), random_state=random_state)
        db = davies_bouldin_score(X, labels)
        silhouettes.append(sil)
        db_scores.append(db)
        print(f"  {k:>3} {km.inertia_:>12.1f} {sil:>12.4f} {db:>16.4f}")

    # Elbow detection: max second derivative of inertia
    inertia_arr = np.array(inertias)
    d2 = np.diff(np.diff(inertia_arr))
    elbow_k = list(k_range)[np.argmax(d2) + 1]
    # Silhouette peak
    sil_k = list(k_range)[np.argmax(silhouettes)]
    # Justified k: majority vote / silhouette priority
    justified_k = sil_k  # silhouette is primary criterion
    print(f"\n  Elbow method suggests k={elbow_k}")
    print(f"  Silhouette peak at k={sil_k} (score={max(silhouettes):.4f})")
    print(f"  → JUSTIFIED k={justified_k} (silhouette is primary criterion)")

    if plot_path:
        fig, axes = plt.subplots(1, 3, figsize=(16, 4))
        ks = list(k_range)
        axes[0].plot(ks, inertias, 'b-o', markersize=6)
        axes[0].axvline(elbow_k, color='red', linestyle='--', label=f'Elbow k={elbow_k}')
        axes[0].set_xlabel('k'); axes[0].set_ylabel('Inertia (WCSS)')
        axes[0].set_title('Elbow Method'); axes[0].legend(); axes[0].grid(alpha=0.3)
        axes[1].plot(ks, silhouettes, 'g-o', markersize=6)
        axes[1].axvline(sil_k, color='red', linestyle='--', label=f'Peak k={sil_k}')
        axes[1].set_xlabel('k'); axes[1].set_ylabel('Silhouette Score')
        axes[1].set_title('Silhouette Analysis'); axes[1].legend(); axes[1].grid(alpha=0.3)
        axes[2].plot(ks, db_scores, 'm-o', markersize=6)
        axes[2].axvline(justified_k, color='red', linestyle='--', label=f'Chosen k={justified_k}')
        axes[2].set_xlabel('k'); axes[2].set_ylabel('Davies-Bouldin Score (lower=better)')
        axes[2].set_title('Davies-Bouldin Score'); axes[2].legend(); axes[2].grid(alpha=0.3)
        plt.suptitle(f'K Selection: Elbow={elbow_k} | Silhouette Peak={sil_k} | Chosen k={justified_k}', fontsize=11)
        plt.tight_layout(); plt.savefig(plot_path, dpi=100); plt.close()
        print(f"  Plot saved: {plot_path}")

    results = {str(k): {'inertia': round(inertias[i],2), 'silhouette': round(silhouettes[i],4), 'davies_bouldin': round(db_scores[i],4)}
               for i, k in enumerate(k_range)}
    return results, elbow_k, sil_k, justified_k


def distance_sanity_check(X: pd.DataFrame, k: int, plot_path=None, random_state=42):
    """Verify distances are meaningful after scaling."""
    km = KMeans(n_clusters=k, init='k-means++', n_init=10, random_state=random_state)
    labels = km.fit_predict(X)
    centers = km.cluster_centers_

    # Inter vs intra cluster distances
    inter_dists = []
    for i in range(k):
        for j in range(i+1, k):
            inter_dists.append(np.linalg.norm(centers[i] - centers[j]))
    intra_dists = []
    for i in range(k):
        mask = labels == i
        if mask.sum() > 1:
            pts = X.values[mask]
            dists = np.linalg.norm(pts - centers[i], axis=1)
            intra_dists.extend(dists.tolist())

    ratio = np.mean(inter_dists) / (np.mean(intra_dists) + 1e-9)
    print(f"\n[Distance Sanity] k={k}")
    print(f"  Mean inter-cluster distance : {np.mean(inter_dists):.4f}")
    print(f"  Mean intra-cluster distance : {np.mean(intra_dists):.4f}")
    print(f"  Inter/Intra ratio           : {ratio:.4f}  {'✓ Good separation' if ratio > 1.5 else '⚠ Low separation'}")

    if plot_path:
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.hist(intra_dists, bins=40, alpha=0.6, color='steelblue', label='Intra-cluster', density=True)
        ax.axvline(np.mean(inter_dists), color='red', linestyle='--', label=f'Mean inter-cluster={np.mean(inter_dists):.2f}')
        ax.set_xlabel('Distance'); ax.set_ylabel('Density')
        ax.set_title(f'Distance Sanity Check (k={k}) | ratio={ratio:.2f}')
        ax.legend(); ax.grid(alpha=0.3)
        plt.tight_layout(); plt.savefig(plot_path, dpi=100); plt.close()
        print(f"  Plot saved: {plot_path}")
    return ratio, labels
