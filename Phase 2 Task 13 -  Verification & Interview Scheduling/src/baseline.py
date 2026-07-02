"""
baseline.py

Two baselines to compare against:

1. naive_rule_baseline - reproduces the old per-window rule-based system
   ported to session level: if *any* window crossed any threshold, flag the
   whole session. This is the thing that caused the 69% FP rate we're trying
   to fix. Kept as a standalone function so the metrics table can show the
   starting point honestly.

2. LogregBaseline - a session-level logistic regression on the Task 11
   feature set only (no new session-context features). Intermediate baseline:
   better than naive rules, but still missing the flag_window_ratio,
   flags_clustered, and score_drop_pct signals Task 13 adds.

Having two baselines makes the improvement story verifiable in steps rather
than a single black-box "before vs after".
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Features available in Task 11's window-level model, aggregated to session level
TASK11_FEATURES = [
    "total_eye_away_sec",
    "total_face_missing_sec",
    "total_tab_switches",
    "total_focus_loss",
    "any_multi_face_detected",
    "audio_voice_window_count",
    "avg_head_pose_deviation_deg",
]

# the new session-context features Task 13 introduces on top of the above
SESSION_FEATURES = TASK11_FEATURES + [
    "flag_window_ratio",
    "flags_clustered",
    "score_drop_pct",
]

# rough session-level thresholds mirroring the per-window rule set from Task 11
NAIVE_THRESHOLDS = {
    "total_eye_away_sec": 30,
    "total_face_missing_sec": 12,
    "total_tab_switches": 12,
    "any_multi_face_detected": 1,
    "audio_voice_window_count": 1,
}


def naive_rule_flag(row):
    """Session-level port of the old OR-of-rules. Returns (flagged, triggered)."""
    triggered = []
    if row["total_eye_away_sec"] > NAIVE_THRESHOLDS["total_eye_away_sec"]:
        triggered.append(f"total eye-away {row['total_eye_away_sec']:.0f}s (>{NAIVE_THRESHOLDS['total_eye_away_sec']}s)")
    if row["total_face_missing_sec"] > NAIVE_THRESHOLDS["total_face_missing_sec"]:
        triggered.append(f"face missing {row['total_face_missing_sec']:.0f}s (>{NAIVE_THRESHOLDS['total_face_missing_sec']}s)")
    if row["total_tab_switches"] > NAIVE_THRESHOLDS["total_tab_switches"]:
        triggered.append(f"tab switches {row['total_tab_switches']} (>{NAIVE_THRESHOLDS['total_tab_switches']})")
    if row["any_multi_face_detected"] == 1:
        triggered.append("multiple faces detected during session")
    if row["audio_voice_window_count"] > 0:
        triggered.append(f"voice detected in {row['audio_voice_window_count']} window(s)")
    return len(triggered) > 0, triggered


def naive_predict(df):
    return df.apply(lambda r: int(naive_rule_flag(r)[0]), axis=1)


class LogregBaseline:
    """Session-level logistic regression on Task 11 features only."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.clf = LogisticRegression(max_iter=1000, class_weight="balanced")
        self.threshold = 0.5

    def fit(self, train_df, val_df):
        X_tr = train_df[TASK11_FEATURES].astype(float).values
        y_tr = train_df["label_cheating"].values
        self.scaler.fit(X_tr)
        self.clf.fit(self.scaler.transform(X_tr), y_tr)
        self.threshold = self._tune_threshold(val_df)

    def _tune_threshold(self, val_df, min_recall=0.82):
        probs = self.predict_proba(val_df)
        y_val = val_df["label_cheating"].values
        best_t, best_fpr = 0.5, 1.0
        for t in np.arange(0.05, 0.96, 0.01):
            preds = (probs >= t).astype(int)
            tp = ((preds == 1) & (y_val == 1)).sum()
            fn = ((preds == 0) & (y_val == 1)).sum()
            fp = ((preds == 1) & (y_val == 0)).sum()
            tn = ((preds == 0) & (y_val == 0)).sum()
            recall = tp / (tp + fn) if (tp + fn) else 0
            fpr = fp / (fp + tn) if (fp + tn) else 1
            if recall >= min_recall and fpr < best_fpr:
                best_fpr = fpr
                best_t = t
        return round(float(best_t), 3)

    def predict_proba(self, df):
        X = df[TASK11_FEATURES].astype(float).values
        return self.clf.predict_proba(self.scaler.transform(X))[:, 1]

    def predict(self, df):
        return (self.predict_proba(df) >= self.threshold).astype(int)
