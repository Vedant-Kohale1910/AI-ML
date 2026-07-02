"""
data_gen.py

Task 13's upstream dependency is "flagged-session data" — not raw per-window
events like Task 11, but sessions that the old rule-based system already
flagged, each with a human-reviewer's final call on whether they were
actually cheating. This is the key structural difference from Task 11:

  Task 11 data: every monitoring window, labelled from the synthetic archetypes
  Task 13 data: only sessions the baseline flagged, labelled by a human after the fact

That last part matters for FP reduction. The input here is a biased sample —
the baseline only ever sends flagged sessions to human review, so every row in
this dataset got triggered by at least one rule. The distribution of true
positives vs false positives within that flagged pool is the exact thing we
need to get right.

Features here are SESSION-level, not window-level. Instead of "this 60-second
window had 3 tab switches", we have "across the student's whole 45-minute
session, tab switches totalled 18, with 6 distinct windows flagged, and the
flags were clustered in the last 20 minutes". Session-level context is
information the window-level model in Task 11 couldn't use, and it's the
main mechanism for further FP reduction: a student who scratches their head
once during a 45-minute test produces one flagged window out of 9 — very
different from a student who produces 8 flagged windows out of 9.

Run:
    python src/data_gen.py
"""

import random
import numpy as np
import pandas as pd

SEED = 55
random.seed(SEED)
np.random.seed(SEED)

N_FLAGGED_SESSIONS = 1200

# roughly what fraction of flagged sessions are actually cheating, based
# on the Task 11 baseline's known FPR of 0.26. most of what the old
# rule-based system flagged was honest behaviour - that's the whole problem.
TRUE_CHEATING_RATE = 0.31


def _trunc_norm(mean, std, lo, hi, size=1):
    return float(np.clip(np.random.normal(mean, std, size=size)[0], lo, hi))


def _gen_session(is_cheating):
    """One full assessment session (not a single window). The extra
    session-level features are what Task 13 adds over Task 11."""
    n_windows = random.randint(4, 10)

    if is_cheating:
        # cheating sessions have many flagged windows, clustered toward
        # the middle/end of the assessment (when the questions get harder
        # and the material they're referencing matters more)
        n_flagged = random.randint(max(1, n_windows - 3), n_windows)
        flags_clustered = 1 if random.random() < 0.75 else 0

        total_eye_away = _trunc_norm(n_flagged * 18, 8, 5, n_flagged * 45)
        total_face_missing = _trunc_norm(n_flagged * 4, 3, 0, n_flagged * 15)
        total_tab_switches = int(np.random.poisson(n_flagged * 5.5))
        total_focus_loss = int(np.random.poisson(n_flagged * 4))
        any_multi_face = 1 if random.random() < 0.35 else 0
        audio_voice_windows = random.randint(0, min(n_flagged, 3))
        avg_head_pose = _trunc_norm(30, 10, 8, 70)
        score_drop_pct = _trunc_norm(-18, 10, -50, 5)  # performance usually drops when cheating helps less near end
    else:
        # honest but flagged: one unusual moment, environment noise, or
        # a naturally fidgety test-taker who kept triggering single rules
        n_flagged = random.randint(1, max(1, n_windows // 3))
        flags_clustered = 1 if random.random() < 0.20 else 0  # honest oddities are usually isolated

        total_eye_away = _trunc_norm(n_flagged * 6, 4, 0, n_flagged * 18)
        total_face_missing = _trunc_norm(n_flagged * 3.5, 3, 0, n_flagged * 12)
        total_tab_switches = int(np.random.poisson(n_flagged * 1.2))
        total_focus_loss = int(np.random.poisson(n_flagged * 0.9))
        any_multi_face = 1 if random.random() < 0.06 else 0
        audio_voice_windows = random.randint(0, min(n_flagged, 2))
        avg_head_pose = _trunc_norm(14, 6, 0, 35)
        score_drop_pct = _trunc_norm(2, 8, -15, 20)  # honest students' performance is flat or improves

    flag_ratio = round(n_flagged / n_windows, 3)

    return {
        "n_windows": n_windows,
        "n_flagged_windows": n_flagged,
        "flag_window_ratio": flag_ratio,
        "flags_clustered": flags_clustered,
        "total_eye_away_sec": round(total_eye_away, 1),
        "total_face_missing_sec": round(total_face_missing, 1),
        "total_tab_switches": total_tab_switches,
        "total_focus_loss": total_focus_loss,
        "any_multi_face_detected": any_multi_face,
        "audio_voice_window_count": audio_voice_windows,
        "avg_head_pose_deviation_deg": round(avg_head_pose, 1),
        "score_drop_pct": round(score_drop_pct, 1),
        "label_cheating": int(is_cheating),
    }


def make_dataset():
    n_cheating = round(N_FLAGGED_SESSIONS * TRUE_CHEATING_RATE)
    n_honest = N_FLAGGED_SESSIONS - n_cheating

    rows = []
    session_id = 1
    for _ in range(n_cheating):
        row = _gen_session(is_cheating=True)
        row["session_id"] = f"FS{session_id:05d}"
        rows.append(row)
        session_id += 1
    for _ in range(n_honest):
        row = _gen_session(is_cheating=False)
        row["session_id"] = f"FS{session_id:05d}"
        rows.append(row)
        session_id += 1

    df = pd.DataFrame(rows)
    # column order
    cols = ["session_id", "n_windows", "n_flagged_windows", "flag_window_ratio",
            "flags_clustered", "total_eye_away_sec", "total_face_missing_sec",
            "total_tab_switches", "total_focus_loss", "any_multi_face_detected",
            "audio_voice_window_count", "avg_head_pose_deviation_deg",
            "score_drop_pct", "label_cheating"]
    df = df[cols].sample(frac=1, random_state=SEED).reset_index(drop=True)

    # student-level split (one session per student, so this is equivalent)
    n = len(df)
    n_train = round(n * 0.65)
    n_val = round(n * 0.15)
    splits = ["train"] * n_train + ["val"] * n_val + ["test"] * (n - n_train - n_val)
    random.shuffle(splits)
    df["split"] = splits
    return df


if __name__ == "__main__":
    df = make_dataset()
    df.to_csv("data/flagged_sessions.csv", index=False)
    print(f"wrote {len(df)} rows -> data/flagged_sessions.csv")
    print(df["split"].value_counts())
    print()
    print("label balance:")
    print(df["label_cheating"].value_counts(normalize=True).round(3))
    print()
    print("cheating rate by split:")
    print(df.groupby("split")["label_cheating"].mean().round(3))
