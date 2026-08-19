import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def compute_diversity(predictions: dict, y_true, plot_path: str):
    """Compute pairwise disagreement rates and error correlation."""
    names = list(predictions.keys())
    n = len(names)
    disagree = np.zeros((n, n))
    for i, n1 in enumerate(names):
        for j, n2 in enumerate(names):
            disagree[i, j] = round(np.mean(predictions[n1] != predictions[n2]), 4)

    print("\n[Diversity] Pairwise Disagreement Rates:")
    df = pd.DataFrame(disagree, index=names, columns=names)
    print(df.round(4).to_string())

    # Error overlap
    errors = {n: (predictions[n] != y_true.values) for n in names}
    overlap_matrix = np.zeros((n, n))
    for i, n1 in enumerate(names):
        for j, n2 in enumerate(names):
            both_wrong = np.sum(errors[n1] & errors[n2])
            either_wrong = np.sum(errors[n1] | errors[n2])
            overlap_matrix[i, j] = round(both_wrong / (either_wrong + 1e-9), 4)

    print("\n[Diversity] Error Overlap (Jaccard, lower=more diverse):")
    df2 = pd.DataFrame(overlap_matrix, index=names, columns=names)
    print(df2.round(4).to_string())

    # Plot disagreement heatmap
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, mat, title in zip(axes, [disagree, overlap_matrix], ['Disagreement Rate', 'Error Overlap (Jaccard)']):
        im = ax.imshow(mat, cmap='YlOrRd', vmin=0, vmax=1)
        ax.set_xticks(range(n)); ax.set_yticks(range(n))
        ax.set_xticklabels(names, rotation=30, ha='right', fontsize=9)
        ax.set_yticklabels(names, fontsize=9)
        for ii in range(n):
            for jj in range(n):
                ax.text(jj, ii, f'{mat[ii,jj]:.2f}', ha='center', va='center', fontsize=9)
        ax.set_title(title)
        plt.colorbar(im, ax=ax)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=100)
    plt.close()
    print(f"[Diversity] Plot saved: {plot_path}")
    return df, df2


def diminishing_returns(models_ordered: list, X_test, y_test, plot_path: str):
    """Show how F1 changes as we add more models via simple voting."""
    from sklearn.metrics import f1_score
    results = []
    for k in range(1, len(models_ordered) + 1):
        preds = np.array([m.predict(X_test) for m in models_ordered[:k]])
        vote = (preds.mean(axis=0) >= 0.5).astype(int)
        results.append({'n_models': k, 'f1': round(f1_score(y_test, vote, zero_division=0), 4)})
    fig, ax = plt.subplots(figsize=(6, 4))
    xs = [r['n_models'] for r in results]
    ys = [r['f1'] for r in results]
    ax.plot(xs, ys, 'o-', color='steelblue', linewidth=2)
    ax.set_xlabel('Number of Models'); ax.set_ylabel('F1 Score')
    ax.set_title('Diminishing Returns: Adding More Models')
    ax.set_xticks(xs)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=100)
    plt.close()
    print(f"[Diversity] Diminishing returns plot saved: {plot_path}")
    for r in results:
        print(f"  {r['n_models']} model(s): F1={r['f1']}")
    return results
