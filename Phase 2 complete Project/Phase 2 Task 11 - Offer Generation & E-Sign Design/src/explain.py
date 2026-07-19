"""
explain.py

Turns a probability into something a non-ML reviewer (or a candidate
disputing a flag) can actually read. No "trust the model" - every
prediction comes with which signals pushed it up, by how much, and what
"normal" looks like for that signal.

Contribution of a feature = its standardised coefficient * its
standardised value for this event. Sign and magnitude both matter:
positive and large means "this signal is doing most of the work in
pushing the score toward cheating".
"""

import numpy as np

from baseline import FEATURES

READABLE_NAMES = {
    "eye_away_duration_sec": "looked away from the screen",
    "face_missing_duration_sec": "face not visible to the camera",
    "tab_switch_count": "switched browser tabs",
    "window_focus_loss_count": "switched away from the assessment window",
    "multiple_faces_detected": "more than one face detected",
    "audio_voice_detected": "voice/conversation picked up",
    "head_pose_deviation_deg": "head turned away from the screen",
}

UNITS = {
    "eye_away_duration_sec": "s", "face_missing_duration_sec": "s",
    "tab_switch_count": "x", "window_focus_loss_count": "x",
    "head_pose_deviation_deg": "deg",
}


def _format_value(feature, value):
    if feature in ("multiple_faces_detected", "audio_voice_detected"):
        return "yes" if value else "no"
    return f"{value:g}{UNITS.get(feature, '')}"


def explain_prediction(features: dict, bundle: dict):
    """features: dict of the 7 raw signals for one window.
    bundle: the loaded joblib bundle from model.py.
    Returns suspicion_score, status, and a ranked, plain-English reason."""

    clf, scaler = bundle["model"], bundle["scaler"]
    low_t, high_t = bundle["low_threshold"], bundle["high_threshold"]
    normal_p95 = bundle["normal_p95"]

    x_raw = np.array([[features[f] for f in FEATURES]], dtype=float)
    x_scaled = scaler.transform(x_raw)[0]
    prob = float(clf.predict_proba(x_scaled.reshape(1, -1))[0, 1])

    if prob >= high_t:
        status = "FLAGGED"
    elif prob >= low_t:
        status = "REVIEW"
    else:
        status = "SAFE"

    contributions = []
    for i, f in enumerate(FEATURES):
        contrib = float(clf.coef_[0][i] * x_scaled[i])
        contributions.append((f, contrib, features[f]))
    contributions.sort(key=lambda c: c[1], reverse=True)

    reasons = []
    for f, contrib, value in contributions:
        if contrib <= 0.05:
            continue  # not meaningfully pushing the score up, skip it
        above_normal = value > normal_p95[f] if f not in ("multiple_faces_detected", "audio_voice_detected") else value == 1
        if not above_normal:
            continue
        readable = READABLE_NAMES[f]
        val_str = _format_value(f, value)
        if f in normal_p95 and f not in ("multiple_faces_detected", "audio_voice_detected"):
            normal_str = f"{normal_p95[f]:g}{UNITS.get(f, '')}"
            reasons.append(f"{readable} ({val_str}, typical honest range is under {normal_str})")
        else:
            reasons.append(f"{readable}")

    if not reasons:
        reason_text = "no signal stood out above what's typical for an honest test-taker"
    else:
        reason_text = "; ".join(reasons[:3])  # top 3 is plenty for a human reading this

    return {
        "suspicion_score": round(prob, 3),
        "status": status,
        "reason": reason_text,
        "top_contributors": [
            {"feature": f, "value": v, "contribution": round(c, 3)}
            for f, c, v in contributions[:3]
        ],
    }
