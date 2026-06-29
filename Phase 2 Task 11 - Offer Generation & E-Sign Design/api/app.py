"""
api/app.py

Serving layer for the hardened proctoring detector. Loads the model
bundle built by src/model.py, scores incoming events, and returns a
three-way status plus the plain-English reason - not just a yes/no.

Run from the project root:
    uvicorn api.app:app --reload --port 8003

Try it:
    curl -X POST http://localhost:8003/check \
        -H "Content-Type: application/json" \
        -d '{"eye_away_duration_sec": 9.5, "face_missing_duration_sec": 1.0, "tab_switch_count": 1, "window_focus_loss_count": 1, "multiple_faces_detected": 0, "audio_voice_detected": 0, "head_pose_deviation_deg": 12}'
"""

import os
import sys

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from explain import explain_prediction  # noqa: E402
from baseline import baseline_flag, FEATURES  # noqa: E402

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "proctoring_model.pkl")

app = FastAPI(title="PlaceMux Proctoring Hardening API", version="0.1.0")

_bundle = None


def get_bundle():
    global _bundle
    if _bundle is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(f"no model at {MODEL_PATH} - run `python src/model.py` first")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


class CheckRequest(BaseModel):
    eye_away_duration_sec: float
    face_missing_duration_sec: float
    tab_switch_count: int
    window_focus_loss_count: int = 0
    multiple_faces_detected: int = 0
    audio_voice_detected: int = 0
    head_pose_deviation_deg: float = 0.0
    include_baseline_comparison: bool = False


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": os.path.exists(MODEL_PATH)}


@app.post("/check")
def check(req: CheckRequest):
    bundle = get_bundle()
    features = {f: getattr(req, f) for f in FEATURES}

    result = explain_prediction(features, bundle)
    response = {
        "suspicion_score": result["suspicion_score"],
        "status": result["status"],
        "reason": result["reason"],
        "top_contributors": result["top_contributors"],
    }

    if req.include_baseline_comparison:
        # mostly useful for demos - shows what the old rule-based system
        # would have done with the exact same input.
        flagged, triggered = baseline_flag(features)
        response["baseline_comparison"] = {
            "would_flag_as_cheating": flagged,
            "triggered_rules": triggered,
        }

    return response
