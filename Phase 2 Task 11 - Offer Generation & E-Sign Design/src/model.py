"""
model.py

The "hardened" detector. Instead of OR-ing rules, this fits a logistic
regression over all the signals together, so e.g. a single brief face
dropout doesn't carry the same weight as a face dropout PLUS tab
switching PLUS a second voice. Logistic regression specifically because
the coefficients double as the explanation - no separate "explainability
layer" bolted on after the fact.

Output isn't binary. Two tuned thresholds split the probability into
three bands:
    SAFE     - below low threshold, no action
    REVIEW   - in between - genuinely ambiguous, route to a human
                proctor instead of auto-flagging
    FLAGGED  - above high threshold - confident enough to flag automatically

The REVIEW band is the actual point of "hardening" here: a lot of what
used to be a hard false positive now becomes "ask a person to glance at
it", which is a much smaller cost than wrongly flagging an honest
student outright.

Both thresholds are picked on the validation split only - never the test
split - same discipline as Task 7/9/10.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from baseline import FEATURES

MODEL_PATH = "../models/proctoring_model.pkl"


def prepare_xy(df):
    X = df[FEATURES].astype(float).values
    y = df["label_cheating"].astype(int).values
    return X, y


def train_logistic(train_df):
    X_train, y_train = prepare_xy(train_df)

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # class_weight='balanced' because cheating is the minority class
    # (~17% here) and we'd rather the model actually learn that signal
    # than learn "always predict 0 and be 83% right".
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    clf.fit(X_train_scaled, y_train)

    return clf, scaler


def score(clf, scaler, df):
    X, _ = prepare_xy(df)
    X_scaled = scaler.transform(X)
    return clf.predict_proba(X_scaled)[:, 1]


def tune_thresholds(clf, scaler, val_df, min_recall=0.85, review_band_width=0.25):
    """Pick the FLAGGED threshold as the lowest cutoff that still keeps
    recall >= min_recall on validation (we'd rather review a few extra
    borderline cases than silently let real cheating through), then set
    the SAFE/REVIEW boundary a fixed band below that. Falls back to 0.5
    if nothing hits the recall floor (shouldn't happen with this data,
    but don't want a silent NaN threshold if it ever does)."""
    y_val = val_df["label_cheating"].values
    probs = score(clf, scaler, val_df)

    candidates = np.arange(0.05, 0.96, 0.01)
    best_high = 0.5
    best_fpr = 1.0
    found = False

    for t in candidates:
        preds = (probs >= t).astype(int)
        tp = ((preds == 1) & (y_val == 1)).sum()
        fn = ((preds == 0) & (y_val == 1)).sum()
        fp = ((preds == 1) & (y_val == 0)).sum()
        tn = ((preds == 0) & (y_val == 0)).sum()

        recall = tp / (tp + fn) if (tp + fn) else 0
        fpr = fp / (fp + tn) if (fp + tn) else 0

        if recall >= min_recall and fpr < best_fpr:
            best_fpr = fpr
            best_high = t
            found = True

    high_threshold = best_high if found else 0.5
    low_threshold = max(0.02, high_threshold - review_band_width)
    return round(float(low_threshold), 3), round(float(high_threshold), 3)


def classify(p, low_threshold, high_threshold):
    if p >= high_threshold:
        return "FLAGGED"
    if p >= low_threshold:
        return "REVIEW"
    return "SAFE"


def main():
    events_df = pd.read_csv("../data/proctoring_events.csv")
    train_df = events_df[events_df["split"] == "train"]
    val_df = events_df[events_df["split"] == "val"]

    clf, scaler = train_logistic(train_df)
    low_threshold, high_threshold = tune_thresholds(clf, scaler, val_df)

    print(f"tuned thresholds -> SAFE < {low_threshold} <= REVIEW < {high_threshold} <= FLAGGED")
    print("feature coefficients (standardised):")
    for name, coef in zip(FEATURES, clf.coef_[0]):
        print(f"  {name:30s} {coef:+.3f}")

    # what "normal" looks like, in the actual units a person reads -
    # 95th percentile of the honest (label=0) training windows. Used by
    # explain.py to say "18.2s, vs a normal range of 0-7.4s" instead of
    # just a bare coefficient.
    honest_train = train_df[train_df["label_cheating"] == 0]
    normal_p95 = {f: round(float(honest_train[f].quantile(0.95)), 1) for f in FEATURES}

    bundle = {
        "model": clf,
        "scaler": scaler,
        "features": FEATURES,
        "low_threshold": low_threshold,
        "high_threshold": high_threshold,
        "normal_p95": normal_p95,
        "trained_on": "synthetic proctoring_events.csv v1",
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"\nsaved model -> {MODEL_PATH}")


if __name__ == "__main__":
    main()
