import json
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from explain import explain_match, batch_explain
from match import load_students, load_jobs, rank_candidates_for_job
from metrics import evaluate

app = FastAPI(
    title="PlaceMux — Job Matching API",
    description="Skill-based job matching with explainability for every decision.",
    version="1.0.0",
)


# request/response models

class MatchRequest(BaseModel):
    student_id: int
    job_id: int


class InlineMatchRequest(BaseModel):
    student: dict
    job: dict


# helpers

def _get_student(student_id: int):
    students = load_students()
    student = next((s for s in students if s["id"] == student_id), None)
    if student is None:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found.")
    return student


def _get_job(job_id: int):
    jobs = load_jobs()
    job = next((j for j in jobs if j["id"] == job_id), None)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")
    return job


# routes

@app.get("/")
def root():
    return {"message": "PlaceMux Matching API is running. Visit /docs for the full API."}


@app.post("/match")
def match_student_to_job(req: MatchRequest):

    student = _get_student(req.student_id)
    job     = _get_job(req.job_id)
    result  = explain_match(student, job)
    return JSONResponse(content=result)


@app.post("/match/inline")
def match_inline(req: InlineMatchRequest):
    try:
        result = explain_match(req.student, req.job)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return JSONResponse(content=result)


@app.get("/jobs")
def list_jobs():
    return load_jobs()


@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    return _get_job(job_id)


@app.get("/students")
def list_students():
    return load_students()


@app.get("/students/{student_id}")
def get_student(student_id: int):
    return _get_student(student_id)


@app.get("/rankings/{job_id}")
def get_rankings(job_id: int, top_n: int = 5):
    job      = _get_job(job_id)
    students = load_students()
    ranked   = rank_candidates_for_job(job, students)

    output = []
    for rank, (student, score) in enumerate(ranked[:top_n], 1):
        explanation = explain_match(student, job)
        output.append({"rank": rank, **explanation})

    return output


@app.get("/metrics")
def get_metrics(threshold: float = 60.0):
    students = load_students()
    jobs     = load_jobs()
    results  = evaluate(students, jobs, threshold=threshold)
    return results
