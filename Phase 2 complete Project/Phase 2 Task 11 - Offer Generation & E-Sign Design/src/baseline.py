"""
baseline.py

This is meant to be roughly what's already running in production - flag
on any single signal crossing a low bar. Nobody designed it to be this
trigger-happy on purpose, it just grew rule by rule every time someone
asked "can we also flag X", and nobody went back to check what it does
to honest students. That's the thing this task is hardening.

Every one of these thresholds is individually defensible (more than 2
tab switches in a minute IS unusual) - the problem is OR-ing five
individually-reasonable rules together multiplies the false-positive
rate, it doesn't average it out.
"""

FEATURES = [
    "eye_away_duration_sec", "face_missing_duration_sec", "tab_switch_count",
    "window_focus_loss_count", "multiple_faces_detected", "audio_voice_detected",
    "head_pose_deviation_deg",
]


def baseline_flag(row):
    """row is a dict or pandas Series with the FEATURES above. Returns
    (flagged: bool, triggered_rules: list[str]) so the same function can
    drive both the metric and the explanation."""
    triggered = []

    if row["eye_away_duration_sec"] > 5:
        triggered.append(f"looked away for {row['eye_away_duration_sec']}s (>5s)")
    if row["face_missing_duration_sec"] > 2:
        triggered.append(f"face not visible for {row['face_missing_duration_sec']}s (>2s)")
    if row["tab_switch_count"] > 2:
        triggered.append(f"switched tabs {row['tab_switch_count']} times (>2)")
    if row["multiple_faces_detected"] == 1:
        triggered.append("more than one face detected")
    if row["audio_voice_detected"] == 1:
        triggered.append("voice/conversation detected")

    return (len(triggered) > 0), triggered


def baseline_predict(df):
    """Vectorised-ish wrapper for a dataframe - returns a 0/1 series."""
    return df.apply(lambda r: int(baseline_flag(r)[0]), axis=1)
