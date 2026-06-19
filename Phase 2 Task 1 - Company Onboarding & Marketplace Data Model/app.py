from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
import pandas as pd
import os

from matching import (
    calculate_match,
    top_jobs_for_student,
    top_students_for_job,
    evaluate_matching,
    feature_space_summary,
    MatchResult,
)

app = FastAPI(
    title="PlaceMux Matching API",
    description="Student-job matching engine for PlaceMux",
    version="1.0.0",
)

# load csvs once on startup
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

students_df = pd.read_csv(os.path.join(DATA_DIR, "students.csv"))
jobs_df = pd.read_csv(os.path.join(DATA_DIR, "jobs.csv"))


# request/response models

class MatchRequest(BaseModel):
    student_id: int
    job_id: int


class SkillMatchRequest(BaseModel):
    job_id: int
    student_skills: Dict[str, float]
    projects: Optional[int] = None
    internships: Optional[int] = None
    cgpa: Optional[float] = None


class MatchResponse(BaseModel):
    student_id: int
    job_id: int
    match_score: float
    skill_score: float
    profile_score: float
    status: str
    matched_skills: List[str]
    missing_skills: List[str]
    reason: List[str]
    warnings: List[str]


class TopJobsRequest(BaseModel):
    student_id: int
    top_n: int = 5


class TopStudentsRequest(BaseModel):
    job_id: int
    top_n: int = 5


class MetricsResponse(BaseModel):
    threshold: float
    precision: float
    recall: float
    false_positive_rate: float
    f1_score: float
    coverage_pct: float
    baseline_precision: float
    improvement_vs_baseline: float
    total_pairs: int
    predicted_matches: int
    true_positives: int
    false_positives: int
    false_negatives: int
    true_negatives: int


def to_response(r: MatchResult) -> MatchResponse:
    return MatchResponse(
        student_id=r.student_id,
        job_id=r.job_id,
        match_score=r.match_score,
        skill_score=r.skill_score,
        profile_score=r.profile_score,
        status=r.status,
        matched_skills=r.matched_skills,
        missing_skills=r.missing_skills,
        reason=r.reason,
        warnings=r.warnings,
    )


@app.get("/health")
def health():
    return {"status": "ok", "students": len(students_df), "jobs": len(jobs_df)}


@app.post("/match", response_model=MatchResponse)
def match_by_id(req: MatchRequest):
    """match a student to a job using their IDs"""
    student_row = students_df[students_df["student_id"] == req.student_id]
    if student_row.empty:
        raise HTTPException(status_code=404, detail=f"student {req.student_id} not found")

    job_row = jobs_df[jobs_df["job_id"] == req.job_id]
    if job_row.empty:
        raise HTTPException(status_code=404, detail=f"job {req.job_id} not found")

    result = calculate_match(student_row.iloc[0], job_row.iloc[0])
    return to_response(result)


@app.post("/match/skills", response_model=MatchResponse)
def match_raw_skills(req: SkillMatchRequest):
    """match raw skill scores to a job - no student record needed"""
    job_row = jobs_df[jobs_df["job_id"] == req.job_id]
    if job_row.empty:
        raise HTTPException(status_code=404, detail=f"job {req.job_id} not found")

    # build a temp student series from the request body
    data = dict(req.student_skills)
    data["student_id"] = -1
    data["projects"] = req.projects or 0
    data["internships"] = req.internships or 0
    data["cgpa"] = req.cgpa or 0.0

    result = calculate_match(pd.Series(data), job_row.iloc[0])
    return to_response(result)


@app.post("/student/top-jobs")
def get_top_jobs(req: TopJobsRequest):
    """returns best matching jobs for a student"""
    student_row = students_df[students_df["student_id"] == req.student_id]
    if student_row.empty:
        raise HTTPException(status_code=404, detail=f"student {req.student_id} not found")

    results = top_jobs_for_student(student_row.iloc[0], jobs_df, top_n=req.top_n)
    return {"student_id": req.student_id, "matches": [to_response(r) for r in results]}


@app.post("/job/top-students")
def get_top_students(req: TopStudentsRequest):
    """returns best matching students for a job posting"""
    job_row = jobs_df[jobs_df["job_id"] == req.job_id]
    if job_row.empty:
        raise HTTPException(status_code=404, detail=f"job {req.job_id} not found")

    results = top_students_for_job(job_row.iloc[0], students_df, top_n=req.top_n)
    return {"job_id": req.job_id, "matches": [to_response(r) for r in results]}


@app.get("/metrics", response_model=MetricsResponse)
def get_metrics(threshold: float = 70.0):
    """precision/recall/f1 across all student-job pairs at given threshold"""
    m = evaluate_matching(students_df, jobs_df, threshold=threshold)
    return MetricsResponse(**m)


@app.get("/feature-space")
def get_feature_space():
    """returns the documented feature space as json"""
    return feature_space_summary().to_dict(orient="records")
