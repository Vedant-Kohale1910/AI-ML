"""
model.py

The improved model that ships in Task 13. Two upgrades over the Task 11
logistic regression:

1. Random Forest instead of logistic regression. At session level, the
   relationship between features isn't linear — a session with a very high
   flag_window_ratio AND audio_voice_window_count > 0 is much more suspicious
   than either signal alone. RF handles these interactions without needing
   polynomial terms, and it's still interpretable enough for a hiring product
   (feature importances, per-tree voting, no "the number said so").

2. Three new session-context features the Task 11 window model couldn't see:
   - flag_window_ratio: fraction of the session's windows that got flagged.
     The key FP-reduction signal - an honest student with one noisy window out
     of 9 should look very different from a cheater with 8 flagged windows.
   - flags_clustered: were the flagged windows bunched together (typical for
     genuine cheating, when a student found a resource to reference) or spread
     across the session randomly (more typical of environment noise)?
   - score_drop_pct: did the student's performance decline during the session?
     Cheating often shows up in middle/late questions where the material is
     harder; honest students tend to be flat or slightly improving.

Threshold still tuned on validation only, same discipline as Tasks 7-11.
Three-tier output (SAFE/REVIEW/FLAGGED) same as Task 11 — the evaluator
asked this to continue from there, so the UX contract stays the same even
though the underlying model improved.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

from baseline import SESSION_FEATURES

MODEL_PATH = "models/proctoring_model.pkl"


def prepare(df, features):
    return df[features].astype(float).values


def tune_threshold(probs, y_true, min_recall=0.85):
    """Pick the threshold that minimises FPR while keeping recall >= min_recall,
    same criterion as Task 11 — we explicitly don't want to trade away cheating
    detection in order to hit a nice FPR number."""
    best_t, best_fpr = 0.5, 1.0
    for t in np.arange(0.05, 0.96, 0.01):
        preds = (probs >= t).astype(int)
        tp = ((preds == 1) & (y_true == 1)).sum()
        fn = ((preds == 0) & (y_true == 1)).sum()
        fp = ((preds == 1) & (y_true == 0)).sum()
        tn = ((preds == 0) & (y_true == 0)).sum()
        recall = tp / (tp + fn) if (tp + fn) else 0
        fpr = fp / (fp + tn) if (fp + tn) else 1
        if recall >= min_recall and fpr < best_fpr:
            best_fpr = fpr
            best_t = t
    return round(float(best_t), 3), round(float(best_fpr), 3)


def main():
    df = pd.read_csv("data/flagged_sessions.csv")
    train_df = df[df["split"] == "train"]
    val_df = df[df["split"] == "val"]

    X_train = prepare(train_df, SESSION_FEATURES)
    y_train = train_df["label_cheating"].values

    # StandardScaler on RF is optional (trees are scale-invariant) but kept
    # for consistency with Task 11 and because it makes threshold values
    # easier to compare across models.
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    clf = RandomForestClassifier(
        n_estimators=300,
        max_depth=8,
        min_samples_leaf=5,
        class_weight="balanced",
        random_state=55,
    )
    clf.fit(X_train_scaled, y_train)

    val_probs = clf.predict_proba(scaler.transform(prepare(val_df, SESSION_FEATURES)))[:, 1]
    high_threshold, val_fpr = tune_threshold(val_probs, val_df["label_cheating"].values)
    low_threshold = max(0.05, high_threshold - 0.25)

    print(f"tuned thresholds -> SAFE < {low_threshold} <= REVIEW < {high_threshold} <= FLAGGED")
    print(f"val FPR at high threshold: {val_fpr}")
    print("\nfeature importances:")
    for name, imp in sorted(zip(SESSION_FEATURES, clf.feature_importances_), key=lambda x: -x[1]):
        print(f"  {name:35s} {imp:.3f}")

    # compute normal-range p95 from honest training sessions for the explainer
    honest_train = train_df[train_df["label_cheating"] == 0]
    normal_p95 = {f: round(float(honest_train[f].quantile(0.95)), 1) for f in SESSION_FEATURES}

    bundle = {
        "model": clf,
        "scaler": scaler,
        "features": SESSION_FEATURES,
        "low_threshold": low_threshold,
        "high_threshold": high_threshold,
        "normal_p95": normal_p95,
        "model_type": "RandomForestClassifier",
        "trained_on": "flagged_sessions.csv v1 (Task 13)",
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"\nsaved -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
