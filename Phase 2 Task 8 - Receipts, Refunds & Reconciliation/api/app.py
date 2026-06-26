"""
PlaceMux — Spend-Quality Guardrail API
Task 8 | Phase 2 | AI/ML Engineer

Endpoints:
  POST /check-match       → check a student-job pair before payment
  GET  /student/{id}      → get a student's profile
  GET  /job/{id}          → get a job's details
  GET  /metrics           → latest guardrail evaluation metrics
  GET  /health            → simple liveness check
"""

import json
import pickle
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ── paths ─────────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent
MODEL_PATH = BASE / "models" / "matching_model.pkl"
METRICS_PATH = BASE / "logs" / "metrics.json"

# ── load model once at startup ────────────────────────────────────────────────
import sys
sys.path.insert(0, str(BASE))
from models.matching_model import MatchingModel
from models.guardrail import apply_guardrail

def _load_model():
    if not MODEL_PATH.exists():
        raise RuntimeError(
            f"Model not found at {MODEL_PATH}. "
            "Run notebooks/guardrail.py first to train and save it."
        )
    return MatchingModel.load(str(MODEL_PATH))

model: MatchingModel = _load_model()

# ── app ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="PlaceMux Spend-Quality Guardrail API",
    description=(
        "Checks whether a student-job match score is high enough to justify "
        "spending ₹100 on an application. Returns a full decision with reasons."
    ),
    version="1.0.0",
)


# ── request / response schemas ────────────────────────────────────────────────
class MatchRequest(BaseModel):
    student_id: int
    job_id: int

    class Config:
        json_schema_extra = {
            "example": {"student_id": 15, "job_id": 3}
        }


class MatchResponse(BaseModel):
    student_id: int
    job_id: int
    student_name: str
    job_title: str
    company: str
    match_score: float
    status: str
    status_label: str
    message: str
    matched_skills: list
    missing_skills: list
    extra_skills: list
    allow_payment: bool
    application_fee: int
    advice: str


# ── endpoints ─────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": True}


@app.post("/check-match", response_model=MatchResponse)
def check_match(req: MatchRequest):
    """
    Main guardrail endpoint. Call this before showing the payment button.

    - If allow_payment is true  → safe to proceed to checkout
    - If allow_payment is false → show the warning message to the student
    """
    try:
        match_result = model.predict(req.student_id, req.job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

    decision = apply_guardrail(match_result)
    return decision.to_dict()


@app.get("/student/{student_id}")
def get_student(student_id: int):
    """Look up a student's profile by ID."""
    if student_id not in model._students:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
    row = model._students[student_id]
    return {
        "student_id": int(row["student_id"]),
        "name": row["name"],
        "skills": row["skills"],
        "experience_years": float(row["experience_years"]),
        "education": row["education"],
    }


@app.get("/job/{job_id}")
def get_job(job_id: int):
    """Look up a job posting by ID."""
    if job_id not in model._jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    row = model._jobs[job_id]
    return {
        "job_id": int(row["job_id"]),
        "title": row["title"],
        "company": row["company"],
        "required_skills": row["required_skills"],
        "min_experience": float(row["min_experience"]),
        "application_fee": int(row["application_fee"]),
        "location": row["location"],
    }


@app.get("/metrics")
def get_metrics():
    """Return the latest guardrail evaluation metrics from the experiment log."""
    if not METRICS_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail="Metrics file not found. Run the notebook to generate it."
        )
    with open(METRICS_PATH) as f:
        return json.load(f)


@app.get("/students")
def list_students(limit: int = 10):
    """Return the first N students for exploration."""
    items = list(model._students.values())[:limit]
    return [
        {
            "student_id": int(r["student_id"]),
            "name": r["name"],
            "skills": r["skills"],
            "education": r["education"],
        }
        for r in items
    ]


@app.get("/jobs")
def list_jobs(limit: int = 10):
    """Return the first N jobs for exploration."""
    items = list(model._jobs.values())[:limit]
    return [
        {
            "job_id": int(r["job_id"]),
            "title": r["title"],
            "company": r["company"],
            "application_fee": int(r["application_fee"]),
        }
        for r in items
    ]


# ── run directly ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
