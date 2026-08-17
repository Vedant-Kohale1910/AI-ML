"""Feature importance analysis and lift measurement."""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score


def get_feature_names(preprocessor, raw_feature_names):
    """Extract feature names after ColumnTransformer."""
    try:
        names = preprocessor.get_feature_names_out()
        # Strip transformer prefix
        clean = [n.split("__", 1)[-1] for n in names]
        return clean
    except Exception:
        return raw_feature_names


def compute_importance(model, feature_names, save_path="results/feature_importance.csv",
                       plot_path="results/feature_importance.png", top_n=20):
    importances = model.feature_importances_
    idx = np.argsort(importances)[::-1][:top_n]
    df = pd.DataFrame({
        "rank":      range(1, len(idx)+1),
        "feature":   [feature_names[i] if i < len(feature_names) else f"feat_{i}" for i in idx],
        "importance": importances[idx].round(4)
    })
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)
    print(f"\n  [Importance] Top {top_n} features:")
    print(df.to_string(index=False))

    # Plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df["feature"][::-1], df["importance"][::-1], color="steelblue", edgecolor="black")
    ax.set_xlabel("Importance"); ax.set_title("Feature Importance (Random Forest)")
    ax.grid(axis="x", alpha=0.3)
    plt.tight_layout()
    plt.savefig(plot_path, dpi=120, bbox_inches="tight"); plt.close()
    print(f"  [Importance] Saved: {plot_path}")
    return df


def measure_lift(X_tr, y_tr, X_val, y_val, feature_sets: dict, seed=42,
                 save_path="results/feature_comparison.csv"):
    """Train RF on each feature set, report F1 lift."""
    rows = []
    for name, (X_tr_p, X_val_p) in feature_sets.items():
        rf = RandomForestClassifier(n_estimators=100, random_state=seed, class_weight="balanced")
        rf.fit(X_tr_p, y_tr)
        pred = rf.predict(X_val_p)
        f1 = round(f1_score(y_val, pred, average="macro"), 4)
        rows.append({"feature_set": name, "val_f1_macro": f1, "n_features": X_tr_p.shape[1]})
        print(f"  {name:30s}  features={X_tr_p.shape[1]:3d}  val_F1={f1}")
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)

    baseline_f1 = df.iloc[0]["val_f1_macro"]
    best_f1     = df["val_f1_macro"].max()
    print(f"\n  [Lift] Raw baseline F1 : {baseline_f1}")
    print(f"  [Lift] Best engineered : {best_f1}  (+{round(best_f1-baseline_f1,4)})")
    return df
