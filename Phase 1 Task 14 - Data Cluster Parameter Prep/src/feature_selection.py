"""Feature selection for clustering: domain-driven + correlation analysis."""
import pandas as pd
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Raw features in the dataset
ALL_FEATURES = ['age','annual_income','spending_score','num_purchases',
                'account_balance','tenure_months','support_calls',
                'region','noise_feature1','noise_feature2']

# Domain-justified selected features (exclude true_segment which is label)
# region = categorical nominal, noise features = known noise to demonstrate exclusion
SELECTED_FEATURES = ['age','annual_income','spending_score','num_purchases','account_balance']
EXCLUDED_FEATURES = ['tenure_months','support_calls','region','noise_feature1','noise_feature2']


def analyze_features(df: pd.DataFrame, plot_path: str = None):
    """Variance, correlation, and selection rationale."""
    feats = [f for f in ALL_FEATURES if f in df.columns]
    stats = df[feats].describe().T
    stats['cv'] = (df[feats].std() / (df[feats].mean().abs() + 1e-9)).round(4)

    print("\n[Feature Selection] Variance & Coefficient of Variation:")
    print(f"  {'Feature':<20} {'Mean':>12} {'Std':>12} {'CV':>8}")
    print(f"  {'-'*56}")
    for f in feats:
        print(f"  {f:<20} {df[f].mean():>12.2f} {df[f].std():>12.2f} {stats.loc[f,'cv']:>8.4f}")

    print(f"\n  Selected : {SELECTED_FEATURES}")
    print(f"  Excluded : {EXCLUDED_FEATURES}")
    print(f"  Rationale: region=nominal categorical (not distance-meaningful);")
    print(f"             tenure/support=low clustering signal; noise*=synthetic noise features")

    if plot_path:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        # Correlation heatmap
        corr = df[feats].corr()
        im = axes[0].imshow(corr.values, cmap='coolwarm', vmin=-1, vmax=1)
        axes[0].set_xticks(range(len(feats))); axes[0].set_yticks(range(len(feats)))
        axes[0].set_xticklabels(feats, rotation=45, ha='right', fontsize=8)
        axes[0].set_yticklabels(feats, fontsize=8)
        for i in range(len(feats)):
            for j in range(len(feats)):
                axes[0].text(j, i, f'{corr.values[i,j]:.2f}', ha='center', va='center', fontsize=7)
        plt.colorbar(im, ax=axes[0])
        axes[0].set_title('Feature Correlation Matrix')
        # CV bar chart
        cvs = [(f, stats.loc[f,'cv']) for f in feats]
        colors = ['#27ae60' if f in SELECTED_FEATURES else '#e74c3c' for f, _ in cvs]
        axes[1].barh([c[0] for c in cvs], [c[1] for c in cvs], color=colors)
        axes[1].set_xlabel('Coefficient of Variation')
        axes[1].set_title('Feature CV (green=selected, red=excluded)')
        plt.tight_layout()
        plt.savefig(plot_path, dpi=100); plt.close()
        print(f"  Plot saved: {plot_path}")
    return SELECTED_FEATURES, EXCLUDED_FEATURES
