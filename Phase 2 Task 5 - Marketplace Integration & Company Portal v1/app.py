"""
app.py
------
FastAPI application for the PlaceMux Matching Engine.
Exposes the full end-to-end flow via REST endpoints.

Endpoints:
  GET  /                         — health check
  POST /match                    — match one student to one job
  POST /rank/candidates          — rank all applicants for a job
  POST /rank/jobs                — rank all jobs for a student
  GET  /validate                 — run full validation and return metrics
  GET  /demo                     — live demo (hardcoded example, as per study guide)
  GET  /metrics                  — return saved metrics report

Run locally: uvicorn app:app --reload
"""

import json
import os
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from matching_engine import compute_match, rank_candidates, rank_jobs_for_student, MATCH_THRESHOLD
from explainability import explain
from metrics import run as run_validation


app = FastAPI(
    title="PlaceMux Matching Engine API",
    description="Validates and ranks student–job matches with explainability.",
    version="1.0.0"
)


# ── Pydantic models ──────────────────────────────────────────────────────────

class StudentInput(BaseModel):
    student_id: str
    name: str
    skills: str                         # pipe-delimited: "Python|ML|SQL"
    cgpa: Optional[float] = 0.0
    experience_months: Optional[int] = 0


class JobInput(BaseModel):
    job_id: str
    role: str
    company: str
    required_skills: str                # pipe-delimited
    min_cgpa: Optional[float] = 0.0
    min_experience_months: Optional[int] = 0


class MatchRequest(BaseModel):
    student: StudentInput
    job: JobInput


class RankCandidatesRequest(BaseModel):
    job: JobInput
    students: list[StudentInput]


class RankJobsRequest(BaseModel):
    student: StudentInput
    jobs: list[JobInput]


# ── Helpers ──────────────────────────────────────────────────────────────────

def _student_dict(s: StudentInput) -> dict:
    return s.model_dump()


def _job_dict(j: JobInput) -> dict:
    return j.model_dump()


# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/", summary="Health check")
def root():
    return {
        "status": "ok",
        "service": "PlaceMux Matching Engine",
        "version": "1.0.0",
        "threshold": MATCH_THRESHOLD
    }


@app.post("/match", summary="Match one student to one job")
def match_endpoint(req: MatchRequest):
    """
    Core endpoint. Given a student and a job, returns:
      - match_score
      - matched_skills
      - missing_skills
      - reason (plain English)
      - prediction (0 or 1)
    """
    result = explain(_student_dict(req.student), _job_dict(req.job))
    return JSONResponse(content=result)


@app.post("/rank/candidates", summary="Rank all applicants for a job")
def rank_candidates_endpoint(req: RankCandidatesRequest):
    """
    Given a job and a list of applicants, return them ranked by match score.
    Deduplicates by student_id automatically.
    """
    students = [_student_dict(s) for s in req.students]
    ranked = rank_candidates(_job_dict(req.job), students)

    return {
        "job_id": req.job.job_id,
        "job_role": req.job.role,
        "total_applicants": len(req.students),
        "after_dedup": len(ranked),
        "threshold": MATCH_THRESHOLD,
        "ranked_candidates": ranked
    }


@app.post("/rank/jobs", summary="Rank all jobs for a student")
def rank_jobs_endpoint(req: RankJobsRequest):
    """
    Given a student, rank all provided jobs by how well the student fits.
    """
    student = _student_dict(req.student)
    jobs = [_job_dict(j) for j in req.jobs]
    ranked = rank_jobs_for_student(student, jobs)

    return {
        "student_id": req.student.student_id,
        "student_name": req.student.name,
        "total_jobs": len(jobs),
        "threshold": MATCH_THRESHOLD,
        "ranked_jobs": ranked
    }


@app.get("/demo", summary="Live demo — hardcoded example")
def demo():
    """
    The live demo example from the study guide.
    One student, one job — full explainability output.
    """
    student = {
        "student_id": "STU_DEMO",
        "name": "Rahul Sharma",
        "skills": "Python|Machine Learning|SQL",
        "cgpa": 8.2,
        "experience_months": 6
    }
    job = {
        "job_id": "JOB_DEMO",
        "role": "ML Engineer",
        "company": "InnoAI Solutions",
        "required_skills": "Python|Machine Learning|Statistics",
        "min_cgpa": 7.0,
        "min_experience_months": 0
    }

    result = explain(student, job)
    return JSONResponse(content={
        "demo": True,
        "student_input": student,
        "job_input": job,
        "matching_output": result,
        "plain_english": result["reason"],
        "verdict": result["verdict"]
    })


@app.get("/validate", summary="Run full validation pipeline")
def validate():
    """
    Runs the complete validation on the pre-built dataset.
    Returns precision, recall, FPR, accuracy, F1.
    This is what the evaluator will call to verify the system works.
    """
    if not os.path.exists("data/validation_dataset.csv"):
        raise HTTPException(
            status_code=400,
            detail="Validation dataset not built yet. Run: python build_validation_dataset.py"
        )
    metrics, _ = run_validation()
    return JSONResponse(content={"validation_metrics": metrics})


@app.get("/metrics", summary="Return saved metrics report")
def metrics_report():
    """Return the most recent saved metrics CSV as JSON."""
    path = "results/metrics_report.csv"
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail="Metrics not yet computed. Run: python metrics.py"
        )
    df = pd.read_csv(path)
    return JSONResponse(content=df.to_dict(orient="records"))


# ── Edge case demo ────────────────────────────────────────────────────────────

@app.get("/edge-cases", summary="Demonstrate edge case handling")
def edge_cases():
    """
    Shows how the engine handles edge cases:
    - No skills listed
    - Missing JD fields
    - Zero overlap
    - Duplicate application (dedup)
    """
    no_skills = compute_match(
        {"student_id": "E1", "name": "No Skills", "skills": "", "cgpa": 7.0, "experience_months": 0},
        {"job_id": "J1", "role": "ML Eng", "company": "Co", "required_skills": "Python|ML",
         "min_cgpa": 6.0, "min_experience_months": 0}
    )
    missing_jd = compute_match(
        {"student_id": "E2", "name": "Jane", "skills": "Python|ML", "cgpa": 8.0, "experience_months": 0},
        {"job_id": "J2", "role": "Unknown", "company": "Co", "required_skills": "",
         "min_cgpa": 6.0, "min_experience_months": 0}
    )
    zero_overlap = compute_match(
        {"student_id": "E3", "name": "Frontend Dev", "skills": "HTML|CSS|React", "cgpa": 9.0, "experience_months": 0},
        {"job_id": "J3", "role": "Data Scientist", "company": "Co",
         "required_skills": "Python|SQL|Statistics", "min_cgpa": 6.0, "min_experience_months": 0}
    )

    dup_student = {"student_id": "E4", "name": "Dup", "skills": "Python", "cgpa": 7.0, "experience_months": 0}
    dup_job = {"job_id": "J4", "role": "Dev", "company": "Co",
               "required_skills": "Python", "min_cgpa": 6.0, "min_experience_months": 0}
    dedup_result = rank_candidates(dup_job, [dup_student, dup_student, dup_student])

    return {
        "no_skills_listed": {"score": no_skills["match_score"], "edge_case": no_skills["edge_case"],
                              "reason": no_skills["reason"]},
        "missing_jd_fields": {"score": missing_jd["match_score"], "edge_case": missing_jd["edge_case"],
                               "reason": missing_jd["reason"]},
        "zero_overlap": {"score": zero_overlap["match_score"], "prediction": zero_overlap["prediction"],
                         "reason": zero_overlap["reason"]},
        "duplicate_application": {
            "sent_count": 3,
            "returned_count": len(dedup_result),
            "note": "Duplicates removed by student_id deduplication"
        }
    }
