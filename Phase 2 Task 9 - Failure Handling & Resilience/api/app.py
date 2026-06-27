"""
api/app.py

This is the thing that actually sits behind "pay ₹100, then apply" -
the matching engine wired into the paywall. Same scoring code as Task 7
(imported from src/matching.py, nothing re-implemented), the new part is
the payment-confirmation gate in front of it and the conversion-check
endpoints for the live demo.

Run from the project root:
    uvicorn api.app:app --reload --port 8001

Try it:
    curl -X POST http://localhost:8001/apply \
        -H "Content-Type: application/json" \
        -d '{"student_id": 1, "skills": "Python,SQL,Machine Learning", "payment_status": "success"}'

    curl http://localhost:8001/conversion-check/9
    curl http://localhost:8001/conversion-check/summary
"""

import os
import sys
import csv
from datetime import datetime, timezone

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from matching import parse_skills, explain_match, rank_jobs, TfidfMatcher  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")
MODEL_PATH = os.path.join(ROOT, "models", "matching_model.pkl")
APPLY_LOG_PATH = os.path.join(ROOT, "reports", "apply_log.csv")
COMPARISON_REPORT_PATH = os.path.join(ROOT, "reports", "comparison_report.csv")
METRICS_REPORT_PATH = os.path.join(ROOT, "reports", "metrics_before_after.csv")

app = FastAPI(title="PlaceMux Conversion-Quality API", version="0.1.0")

_matcher = None
_alpha = None


def get_matcher():
    global _matcher, _alpha
    if _matcher is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(f"no model at {MODEL_PATH} - this should've come from Task 7, not retrained here")
        bundle = joblib.load(MODEL_PATH)
        m = TfidfMatcher.__new__(TfidfMatcher)
        m.jobs_df = bundle["jobs_df"]
        m.job_skill_lists = bundle["job_skill_lists"]
        m.vectorizer = bundle["vectorizer"]
        m.job_matrix = bundle["job_matrix"]
        _matcher = m
        _alpha = bundle["alpha"]
    return _matcher, _alpha


def log_apply_event(student_id, payment_status, outcome, top_job=None):
    """Every apply attempt gets written here - success, failure, edge case,
    all of it. "Handled gracefully" only counts if it's also observable -
    a try/except that swallows the problem silently doesn't satisfy that."""
    os.makedirs(os.path.dirname(APPLY_LOG_PATH), exist_ok=True)
    is_new = not os.path.exists(APPLY_LOG_PATH)
    with open(APPLY_LOG_PATH, "a", newline="") as f:
        writer = csv.writer(f)
        if is_new:
            writer.writerow(["timestamp", "student_id", "payment_status", "outcome", "top_job"])
        writer.writerow([datetime.now(timezone.utc).isoformat(), student_id, payment_status, outcome, top_job or ""])


class ApplyRequest(BaseModel):
    student_id: int
    skills: str
    payment_status: str  # "success" | "failed" | "pending"
    top_n: int | None = 5


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": os.path.exists(MODEL_PATH)}


@app.post("/apply")
def apply(req: ApplyRequest):
    """The actual paywalled endpoint. Matching only ever runs after a
    confirmed payment - that's the contract, and it's the first thing
    checked, before touching the model at all."""
    if req.payment_status != "success":
        # the student's payment didn't go through (or is still pending) -
        # no match gets computed, no compute wasted on it, and it's logged
        # so this isn't a silent drop. The actual money-back / retry logic
        # lives in the payment service, not here - this endpoint's job is
        # just to refuse to run a paid feature on an unpaid request.
        log_apply_event(req.student_id, req.payment_status, "payment_not_confirmed")
        raise HTTPException(
            status_code=402,
            detail=f"payment_status='{req.payment_status}' - matching was not run, nothing was charged for compute that didn't happen",
        )

    student_skills = parse_skills(req.skills)
    if not student_skills:
        # payment went through but the skill snapshot is empty - the
        # profile-sync edge case from make_payment_snapshot.py. Don't
        # silently return an empty/garbage ranking; say so plainly.
        log_apply_event(req.student_id, req.payment_status, "insufficient_profile_data")
        raise HTTPException(
            status_code=422,
            detail="payment confirmed, but no usable skill profile was received - ask the student to retry, don't re-charge them",
        )

    matcher, alpha = get_matcher()
    ranked = rank_jobs(student_skills, matcher, alpha=alpha, top_n=req.top_n or 5)

    log_apply_event(req.student_id, req.payment_status, "ok", top_job=ranked[0]["title"] if ranked else None)
    return {"student_id": req.student_id, "jobs": ranked}


@app.get("/conversion-check/{student_id}")
def conversion_check_one(student_id: int):
    """Live-demo endpoint: this student, before vs after, with the reason -
    pulls from the precomputed comparison report rather than recomputing
    on the fly, so this is exactly what a reviewer would see in reports/."""
    if not os.path.exists(COMPARISON_REPORT_PATH):
        raise HTTPException(status_code=503, detail="run src/compare.py first to build the comparison report")

    df = pd.read_csv(COMPARISON_REPORT_PATH)
    row = df[df["student_id"] == student_id]
    if row.empty:
        raise HTTPException(status_code=404, detail=f"no comparison record for student_id={student_id}")

    return row.iloc[0].where(pd.notnull(row.iloc[0]), None).to_dict()


@app.get("/conversion-check/summary")
def conversion_check_summary():
    """Aggregate verdict - precision/recall/fpr before vs after, plus how
    many students landed in each verdict bucket."""
    if not os.path.exists(METRICS_REPORT_PATH) or not os.path.exists(COMPARISON_REPORT_PATH):
        raise HTTPException(status_code=503, detail="run src/compare.py first")

    metrics_df = pd.read_csv(METRICS_REPORT_PATH)
    comparison_df = pd.read_csv(COMPARISON_REPORT_PATH)

    n_regressions = int((comparison_df["verdict"] == "regression").sum())
    verdict = "NO_REGRESSION" if n_regressions == 0 else "REGRESSION_DETECTED"

    return {
        "verdict": verdict,
        "n_regressions": n_regressions,
        "verdict_breakdown": comparison_df["verdict"].value_counts().to_dict(),
        "metrics": metrics_df.to_dict(orient="records"),
    }
