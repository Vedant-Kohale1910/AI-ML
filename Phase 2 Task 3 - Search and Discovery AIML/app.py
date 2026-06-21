from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd

from ranking import (
    load_data,
    rank_jobs_for_student,
    rank_candidates_for_job,
    explain_job_match,
    explain_candidate_match,
    compute_metrics,
)

app = FastAPI(title="PlaceMux Ranking API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# load once on startup, reuse across requests
students_df, jobs_df = load_data()


class JobRankRequest(BaseModel):
    student_id: Optional[int] = None
    name: Optional[str] = None
    skills: Optional[str] = None
    experience_years: Optional[int] = 0
    communication_score: Optional[int] = 75
    top_n: Optional[int] = 10


class CandidateRankRequest(BaseModel):
    job_id: Optional[int] = None
    title: Optional[str] = None
    required_skills: Optional[str] = None
    min_experience: Optional[int] = 0
    top_n: Optional[int] = 10


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "PlaceMux Ranking API",
        "routes": ["/students", "/jobs", "/rank/jobs", "/rank/candidates",
                   "/metrics/jobs/{id}", "/metrics/candidates/{id}"]
    }


@app.get("/students")
def list_students():
    return students_df.to_dict(orient="records")


@app.get("/students/{student_id}")
def get_student(student_id: int):
    row = students_df[students_df["student_id"] == student_id]
    if row.empty:
        raise HTTPException(404, detail=f"student {student_id} not found")
    return row.iloc[0].to_dict()


@app.get("/jobs")
def list_jobs():
    return jobs_df.to_dict(orient="records")


@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    row = jobs_df[jobs_df["job_id"] == job_id]
    if row.empty:
        raise HTTPException(404, detail=f"job {job_id} not found")
    return row.iloc[0].to_dict()


@app.post("/rank/jobs")
def rank_jobs(req: JobRankRequest):
    if req.student_id is not None:
        row = students_df[students_df["student_id"] == req.student_id]
        if row.empty:
            raise HTTPException(404, detail=f"student {req.student_id} not found")
        student = row.iloc[0].to_dict()
    elif req.skills:
        student = {
            "name": req.name or "Unknown",
            "skills": req.skills,
            "experience_years": req.experience_years or 0,
            "communication_score": req.communication_score or 75,
        }
    else:
        raise HTTPException(400, detail="pass student_id or skills")

    ranked = rank_jobs_for_student(pd.Series(student), jobs_df, top_n=req.top_n)

    explanation = None
    if ranked:
        explanation = explain_job_match(student["name"], ranked[0])

    return {
        "student": student.get("name"),
        "total_ranked": len(ranked),
        "top_match_explanation": explanation,
        "results": ranked,
    }


@app.post("/rank/candidates")
def rank_candidates(req: CandidateRankRequest):
    if req.job_id is not None:
        row = jobs_df[jobs_df["job_id"] == req.job_id]
        if row.empty:
            raise HTTPException(404, detail=f"job {req.job_id} not found")
        job = row.iloc[0].to_dict()
    elif req.required_skills:
        job = {
            "title": req.title or "Custom Job",
            "required_skills": req.required_skills,
            "min_experience": req.min_experience or 0,
        }
    else:
        raise HTTPException(400, detail="pass job_id or required_skills")

    ranked = rank_candidates_for_job(pd.Series(job), students_df, top_n=req.top_n)

    explanation = None
    if ranked:
        explanation = explain_candidate_match(job.get("title"), ranked[0])

    return {
        "job": job.get("title"),
        "total_ranked": len(ranked),
        "top_match_explanation": explanation,
        "results": ranked,
    }


@app.get("/metrics/jobs/{student_id}")
def job_metrics(student_id: int, top_k: int = 5, threshold: float = 60.0):
    row = students_df[students_df["student_id"] == student_id]
    if row.empty:
        raise HTTPException(404, detail=f"student {student_id} not found")

    student = row.iloc[0]
    ranked = rank_jobs_for_student(student, jobs_df)
    m = compute_metrics(ranked, relevance_threshold=threshold, top_k=top_k)

    return {
        "student_id": student_id,
        "student_name": student["name"],
        "metrics": m,
        "notes": {
            "precision": f"{m['precision']*100:.0f}% of top {top_k} were relevant",
            "recall": f"found {m['recall']*100:.0f}% of all relevant jobs",
            "fpr": f"{m['false_positive_rate']*100:.0f}% false positives in top {top_k}",
        }
    }


@app.get("/metrics/candidates/{job_id}")
def candidate_metrics(job_id: int, top_k: int = 5, threshold: float = 60.0):
    row = jobs_df[jobs_df["job_id"] == job_id]
    if row.empty:
        raise HTTPException(404, detail=f"job {job_id} not found")

    job = row.iloc[0]
    ranked = rank_candidates_for_job(job, students_df)
    m = compute_metrics(ranked, relevance_threshold=threshold, top_k=top_k)

    return {
        "job_id": job_id,
        "job_title": job["title"],
        "metrics": m,
        "notes": {
            "precision": f"{m['precision']*100:.0f}% of top {top_k} were relevant",
            "recall": f"found {m['recall']*100:.0f}% of all relevant candidates",
            "fpr": f"{m['false_positive_rate']*100:.0f}% false positives in top {top_k}",
        }
    }
