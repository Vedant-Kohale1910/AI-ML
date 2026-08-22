"""
Task 14 — Data Cluster Parameter Prep
Pipeline: load → feature selection → scaling demo → PCA → k selection → sanity check → save
"""
import sys, os, json, warnings
sys.path.insert(0, os.path.dirname(__file__))
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import joblib

from src.feature_selection import analyze_features, SELECTED_FEATURES, EXCLUDED_FEATURES
from src.scaling import demonstrate_scaling_effect, scale_features
from src.dimensionality import pca_analysis
from src.choose_k import elbow_and_silhouette, distance_sanity_check

DATA = 'data/customer_data.csv'
MODELS_DIR = 'models'
RESULTS_DIR = 'results'
PLOTS_DIR = 'results/plots'

print("="*65)
print("  TASK 14 — DATA CLUSTER PARAMETER PREP PIPELINE")
print("="*65)

# ── STEP 1: Load data ──
print("\n[STEP 1] Loading customer dataset...")
df = pd.read_csv(DATA)
# Drop label column — this is unsupervised
df_features = df.drop(columns=['true_segment'])
print(f"  Rows: {len(df)} | Total features: {len(df_features.columns)}")
print(f"  Columns: {list(df_features.columns)}")
print(f"\n  Dataset summary:")
print(df_features.describe().round(1).to_string())

# ── STEP 2: Feature selection ──
print("\n[STEP 2] Feature selection and analysis...")
selected, excluded = analyze_features(df_features, plot_path=f'{PLOTS_DIR}/feature_analysis.png')
print(f"\n  ✓ Selected {len(selected)} features for clustering: {selected}")
print(f"  ✗ Excluded {len(excluded)} features: {excluded}")

# ── STEP 3: Demonstrate scaling effect ──
print("\n[STEP 3] Demonstrating scaling effect (why unscaled is wrong)...")
X_selected = df[selected].copy()
X_scaled, scaler = demonstrate_scaling_effect(X_selected, selected,
                                               plot_path=f'{PLOTS_DIR}/scaling_comparison.png')
print(f"\n  After StandardScaler: mean≈0, std≈1 for all features")
print(f"  Scaled data shape: {X_scaled.shape}")
print(X_scaled.describe().round(3).to_string())

# ── STEP 4: PCA dimensionality reduction ──
print("\n[STEP 4] PCA dimensionality reduction...")
X_pca, pca, n_components, loadings = pca_analysis(X_scaled, plot_path=f'{PLOTS_DIR}/pca_analysis.png')
print(f"\n  Dimensionality: {len(selected)} features → {n_components} PCA components")
print(f"  Curse of dimensionality: reducing from {len(selected)} to {n_components} dims")
print(f"  Using PCA representation for clustering: {list(X_pca.columns)}")

# ── STEP 5: Choose k (elbow + silhouette) ──
print("\n[STEP 5] Choosing k via elbow method + silhouette score...")
k_results, elbow_k, sil_k, justified_k = elbow_and_silhouette(
    X_pca, k_range=range(2, 11), plot_path=f'{PLOTS_DIR}/k_selection.png')

# ── STEP 6: Distance sanity check ──
print(f"\n[STEP 6] Distance sanity check at chosen k={justified_k}...")
dist_ratio, labels = distance_sanity_check(X_pca, justified_k, plot_path=f'{PLOTS_DIR}/distance_sanity.png')

# ── STEP 7: Cluster size check ──
print(f"\n[STEP 7] Cluster size distribution (k={justified_k})...")
from collections import Counter
size_counts = Counter(labels)
print(f"  {'Cluster':>8} {'Size':>8} {'%':>8}")
print(f"  {'-'*28}")
for c in sorted(size_counts):
    pct = size_counts[c]/len(labels)*100
    print(f"  {c:>8} {size_counts[c]:>8} {pct:>7.1f}%")
min_size = min(size_counts.values())
if min_size < 50:
    print(f"  ⚠ Smallest cluster has only {min_size} records — consider larger k")
else:
    print(f"  ✓ All clusters have ≥{min_size} records — balanced segmentation")

# ── STEP 8: Visualise clusters ──
print(f"\n[STEP 8] Visualising cluster results...")
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
colors = ['#e74c3c','#3498db','#27ae60','#f39c12','#9b59b6','#1abc9c']
for ci in range(justified_k):
    mask = labels == ci
    axes[0].scatter(X_pca['PC1'][mask], X_pca['PC2'][mask],
                    c=colors[ci % len(colors)], alpha=0.5, s=15, label=f'Cluster {ci}')
axes[0].set_xlabel('PC1'); axes[0].set_ylabel('PC2')
axes[0].set_title(f'PCA Clusters (k={justified_k})')
axes[0].legend(markerscale=2, fontsize=8)

for ci in range(justified_k):
    mask = labels == ci
    axes[1].scatter(X_scaled['annual_income'][mask], X_scaled['spending_score'][mask],
                    c=colors[ci % len(colors)], alpha=0.5, s=15, label=f'Cluster {ci}')
axes[1].set_xlabel('Annual Income (scaled)'); axes[1].set_ylabel('Spending Score (scaled)')
axes[1].set_title(f'Income vs Spending (k={justified_k})')
axes[1].legend(markerscale=2, fontsize=8)
plt.suptitle(f'Task 14: Cluster Parameter Prep — k={justified_k}', fontsize=12)
plt.tight_layout(); plt.savefig(f'{PLOTS_DIR}/cluster_visualisation.png', dpi=100); plt.close()

# ── STEP 9: Lock and save prepared dataset + parameters ──
print(f"\n[STEP 9] Saving prepared dataset and cluster parameters...")
# Save scaled + PCA data
X_pca.to_csv(f'{RESULTS_DIR}/prepared_dataset_pca.csv', index=False)
X_scaled.to_csv(f'{RESULTS_DIR}/prepared_dataset_scaled.csv', index=False)

# Save artifacts
joblib.dump(scaler, f'{MODELS_DIR}/scaler.joblib')
joblib.dump(pca, f'{MODELS_DIR}/pca.joblib')

cluster_params = {
    'selected_features': selected,
    'excluded_features': excluded,
    'scaling_method': 'StandardScaler (mean=0, std=1)',
    'pca_n_components': n_components,
    'pca_variance_explained': round(float(np.sum(pca.explained_variance_ratio_)), 4),
    'justified_k': justified_k,
    'elbow_k': elbow_k,
    'silhouette_peak_k': sil_k,
    'silhouette_at_justified_k': k_results[str(justified_k)]['silhouette'],
    'inertia_at_justified_k': k_results[str(justified_k)]['inertia'],
    'davies_bouldin_at_justified_k': k_results[str(justified_k)]['davies_bouldin'],
    'inter_intra_distance_ratio': round(float(dist_ratio), 4),
    'distance_metric': 'Euclidean (default for KMeans)',
    'dataset_rows': len(df),
    'k_sweep_results': k_results,
    'justification': f"k={justified_k} selected because silhouette score peaks at this value ({k_results[str(justified_k)]['silhouette']:.4f}), consistent with elbow in inertia curve at k={elbow_k}. Inter/intra distance ratio={dist_ratio:.2f}>1.5 confirms meaningful cluster separation."
}
with open(f'{RESULTS_DIR}/cluster_parameters.json','w') as f:
    json.dump(cluster_params, f, indent=2)

print(f"  Prepared dataset (PCA) → results/prepared_dataset_pca.csv")
print(f"  Prepared dataset (Scaled) → results/prepared_dataset_scaled.csv")
print(f"  Cluster parameters → results/cluster_parameters.json")
print(f"  Scaler → models/scaler.joblib")
print(f"  PCA → models/pca.joblib")

# ── SUMMARY ──
print(f"\n{'='*65}")
print(f"  CLUSTER PARAMETER SUMMARY")
print(f"{'='*65}")
print(f"  Dataset            : {len(df)} customers, {len(df_features.columns)} raw features")
print(f"  Selected features  : {selected}")
print(f"  Scaling            : StandardScaler → all features comparable")
print(f"  PCA components     : {n_components} (explains {np.sum(pca.explained_variance_ratio_):.1%} variance)")
print(f"  Justified k        : {justified_k}")
print(f"  Silhouette @ k={justified_k}   : {k_results[str(justified_k)]['silhouette']:.4f}")
print(f"  Distance ratio     : {dist_ratio:.2f} (>1.5 = meaningful separation)")
print(f"  Ready for clustering: ✓")
print(f"{'='*65}")
print(f"  Run: python predict.py  for live demo")
