"""
explain.py

Session-level explanation layer. Same philosophy as Task 11's explain.py —
every prediction comes with a ranked, plain-English reason, not just a score.

The difference here is that the features are session-level (accumulated over
a full assessment) rather than per 60-second window, and the top contributors
come from RF feature importances (which vary per-prediction through the
ensemble vote) rather than logistic regression coefficients (which are fixed
per feature). We approximate this with static feature importance from the
fitted forest, which is close enough for a v0 explanation layer and avoids
the complexity of SHAP values at this stage.
"""

from baseline import SESSION_FEATURES

READABLE_NAMES = {
    "total_eye_away_sec": "extended time looking away from the screen",
    "total_face_missing_sec": "extended time face not visible to the camera",
    "total_tab_switches": "high number of browser tab switches across the session",
    "total_focus_loss": "high number of application focus losses",
    "any_multi_face_detected": "another face was detected during the session",
    "audio_voice_window_count": "voice/conversation detected in multiple windows",
    "avg_head_pose_deviation_deg": "head consistently turned away from the screen",
    "flag_window_ratio": "large fraction of the session's windows were flagged",
    "flags_clustered": "flagged windows were clustered together (not isolated noise)",
    "score_drop_pct": "assessment performance declined noticeably during the session",
}

UNITS = {
    "total_eye_away_sec": "s",
    "total_face_missing_sec": "s",
    "avg_head_pose_deviation_deg": "deg",
    "flag_window_ratio": "",
    "score_drop_pct": "%",
}


def _format_val(feat, val):
    binary = ("any_multi_face_detected", "flags_clustered")
    if feat in binary:
        return "yes" if val else "no"
    unit = UNITS.get(feat, "")
    return f"{val:g}{unit}"


def explain_prediction(features: dict, bundle: dict):
    """
    features: dict with the 10 session-level feature values
    bundle: loaded joblib model bundle
    Returns suspicion_score, status, plain-English reason, and top contributors.
    """
    clf = bundle["model"]
    scaler = bundle["scaler"]
    feat_list = bundle["features"]
    low_t = bundle["low_threshold"]
    high_t = bundle["high_threshold"]
    normal_p95 = bundle["normal_p95"]
    importances = dict(zip(feat_list, clf.feature_importances_))

    import numpy as np
    x = np.array([[features[f] for f in feat_list]], dtype=float)
    x_scaled = scaler.transform(x)
    prob = float(clf.predict_proba(x_scaled)[0, 1])

    if prob >= high_t:
        status = "FLAGGED"
    elif prob >= low_t:
        status = "REVIEW"
    else:
        status = "SAFE"

    # build reason from features that are above their honest-session p95,
    # ranked by the RF's feature importance so the most diagnostic signal
    # comes first.
    above_normal = []
    for feat in sorted(importances, key=lambda f: -importances[f]):
        val = features[feat]
        normal_val = normal_p95[feat]
        is_binary = feat in ("any_multi_face_detected", "flags_clustered")

        if is_binary:
            if float(val) == 1.0:
                above_normal.append(READABLE_NAMES[feat])
        else:
            if float(val) > float(normal_val):
                val_str = _format_val(feat, val)
                normal_str = f"{normal_val:g}{UNITS.get(feat, '')}"
                above_normal.append(f"{READABLE_NAMES[feat]} ({val_str}, typical honest is <{normal_str})")

        if len(above_normal) >= 3:
            break

    if not above_normal:
        reason = "no session signal stands out above what's normal for an honest student"
    else:
        reason = "; ".join(above_normal)

    top_contributors = [
        {"feature": f, "value": features[f], "importance": round(float(importances[f]), 3)}
        for f in sorted(importances, key=lambda ff: -importances[ff])[:3]
    ]

    return {
        "suspicion_score": round(prob, 3),
        "status": status,
        "reason": reason,
        "top_contributors": top_contributors,
    }
