"""
api/app.py

Serves the quality sign-off live, so it can be demoed as more than a
notebook printout. Same matching model as Task 7 (loaded straight from
models/matching_model.pkl, nothing retrained here), wrapped with the
sign-off logic from src/signoff.py.

Run from the project root:
    uvicorn api.app:app --reload --port 8002

Try it:
    curl http://localhost:8002/signoff/summary
    curl http://localhost:8002/signoff/1325
    curl -X POST http://localhost:8002/match \
        -H "Content-Type: application/json" \
        -d '{"skills": "Python,SQL,Machine Learning"}'
"""

import os
import sys

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from matching import parse_skills, rank_jobs, TfidfMatcher  # noqa: E402
from signoff import (  # noqa: E402
    run_quality_report, precision_recall_fpr, load_task7_baseline, decide,
)

ROOT = os.path.join(os.path.dirname(__file__), "..")
MODEL_PATH = os.path.join(ROOT, "models", "matching_model.pkl")
STUDENTS_PATH = os.path.join(ROOT, "data", "students.csv")
QUALITY_REPORT_PATH = os.path.join(ROOT, "reports", "quality_report.csv")
FINAL_METRICS_PATH = os.path.join(ROOT, "reports", "final_metrics.csv")

app = FastAPI(title="PlaceMux Quality Sign-off API", version="0.1.0")

_matcher = None
_alpha = None


def get_matcher():
    global _matcher, _alpha
    if _matcher is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(f"no model at {MODEL_PATH} - carried over from Task 7, check it wasn't left behind")
        bundle = joblib.load(MODEL_PATH)
        m = TfidfMatcher.__new__(TfidfMatcher)
        m.jobs_df = bundle["jobs_df"]
        m.job_skill_lists = bundle["job_skill_lists"]
        m.vectorizer = bundle["vectorizer"]
        m.job_matrix = bundle["job_matrix"]
        _matcher = m
        _alpha = bundle["alpha"]
    return _matcher, _alpha


class MatchRequest(BaseModel):
    skills: str
    top_n: int | None = 5


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": os.path.exists(MODEL_PATH)}


@app.post("/match")
def match(req: MatchRequest):
    """Plain matching call, same contract as Task 7's /match - kept here
    too so a reviewer can poke at the live model directly, not just read
    the precomputed report."""
    student_skills = parse_skills(req.skills)
    if not student_skills:
        raise HTTPException(status_code=400, detail="couldn't parse any skills - check formatting (comma separated)")
    matcher, alpha = get_matcher()
    ranked = rank_jobs(student_skills, matcher, alpha=alpha, top_n=req.top_n or 5)
    return {"jobs": ranked}


@app.get("/signoff/{student_id}")
def signoff_one(student_id: int):
    """One student's row from the quality report - the live-demo version
    of 'walk me through this student, this job, and why'."""
    if not os.path.exists(QUALITY_REPORT_PATH):
        raise HTTPException(status_code=503, detail="run src/signoff.py first to build reports/quality_report.csv")

    df = pd.read_csv(QUALITY_REPORT_PATH)
    row = df[df["student_id"] == student_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"no quality-report record for student_id={student_id}")

    return row.iloc[0].where(pd.notnull(row.iloc[0]), None).to_dict()


@app.get("/signoff/summary")
def signoff_summary():
    """The actual sign-off decision, recomputed live against the model and
    data on disk rather than served stale from a cached file - if someone
    swaps in a broken model or a corrupted job feed, this should know."""
    if not os.path.exists(STUDENTS_PATH):
        raise HTTPException(status_code=503, detail="data/students.csv missing - run src/data_gen.py first")

    matcher, alpha = get_matcher()
    students_df = pd.read_csv(STUDENTS_PATH)

    quality_df = run_quality_report(matcher, alpha, students_df)
    current_metrics = precision_recall_fpr(quality_df, matcher, students_df, alpha)
    baseline_metrics = load_task7_baseline()
    verdict = decide(baseline_metrics, current_metrics, quality_df)

    return {
        "decision": verdict["decision"],
        "regression_detected": verdict["regression_detected"],
        "total_students_tested": verdict["total_students_tested"],
        "top1_accuracy": verdict["top1_accuracy"],
        "baseline_metrics": baseline_metrics,
        "current_metrics": current_metrics,
        "precision_drop": verdict["precision_drop"],
    }
