"""
api/app.py

Serving layer for the Task 13 FP-reduction model. Session-level: inputs
are aggregates over a full assessment, not a single 60-second window.

Run from the project root:
    uvicorn api.app:app --reload --port 8005

Try it:
    curl -X POST http://localhost:8005/check \
        -H "Content-Type: application/json" \
        -d '{
              "n_windows": 8, "n_flagged_windows": 1, "flag_window_ratio": 0.125,
              "flags_clustered": 0, "total_eye_away_sec": 6.5,
              "total_face_missing_sec": 12.5, "total_tab_switches": 2,
              "total_focus_loss": 1, "any_multi_face_detected": 0,
              "audio_voice_window_count": 1, "avg_head_pose_deviation_deg": 11.0,
              "score_drop_pct": 3.0, "include_baseline_comparison": true
            }'
"""

import os
import sys

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from explain import explain_prediction  # noqa: E402
from baseline import naive_rule_flag, SESSION_FEATURES  # noqa: E402

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "proctoring_model.pkl")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "..", "reports", "metrics_all_models.csv")

app = FastAPI(title="PlaceMux Proctoring FP Reduction API", version="0.2.0")

_bundle = None


def get_bundle():
    global _bundle
    if _bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError("no model found - run `python src/model.py` first")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


class CheckRequest(BaseModel):
    # session-level features
    n_windows: int
    n_flagged_windows: int
    flag_window_ratio: float
    flags_clustered: int = 0
    total_eye_away_sec: float
    total_face_missing_sec: float
    total_tab_switches: int
    total_focus_loss: int = 0
    any_multi_face_detected: int = 0
    audio_voice_window_count: int = 0
    avg_head_pose_deviation_deg: float = 0.0
    score_drop_pct: float = 0.0
    include_baseline_comparison: bool = False


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": os.path.exists(MODEL_PATH)}


@app.post("/check")
def check(req: CheckRequest):
    bundle = get_bundle()
    features = {f: getattr(req, f) for f in SESSION_FEATURES}

    result = explain_prediction(features, bundle)
    response = {
        "suspicion_score": result["suspicion_score"],
        "status": result["status"],
        "reason": result["reason"],
        "top_contributors": result["top_contributors"],
    }

    if req.include_baseline_comparison:
        flagged, triggered = naive_rule_flag(features)
        response["baseline_naive_rules"] = {
            "would_flag_as_cheating": flagged,
            "triggered_rules": triggered,
        }

    return response


@app.get("/metrics/summary")
def metrics_summary():
    """Returns the test-split metrics for all three models in one call -
    the live version of the 'before vs after' comparison the evaluator wants."""
    if not os.path.exists(METRICS_PATH):
        raise HTTPException(status_code=503, detail="run src/evaluate.py first to build reports")

    import pandas as pd
    df = pd.read_csv(METRICS_PATH)
    test_rows = df[df["split"] == "test"][["model", "precision", "recall", "fpr", "tp", "fp", "fn", "tn"]]
    return test_rows.to_dict(orient="records")
