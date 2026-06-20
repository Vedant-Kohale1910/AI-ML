from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import os
from threshold_validation import validate_by_id, validate_thresholds
from match_vectors import compute_match_by_id, compute_match, rank_students_for_job
from explainability import generate_explanation

app = FastAPI(
    title="PlaceMux Matching API",
    description="Matches students to jobs based on skill vectors and threshold validation.",
    version="1.0.0"
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
SKILL_COLS = ["python", "ml", "sql", "dsa", "statistics", "deep_learning"]


class MatchRequest(BaseModel):
    student_id: int
    job_id: int


class SkillProfile(BaseModel):
    python: Optional[float] = 0
    ml: Optional[float] = 0
    sql: Optional[float] = 0
    dsa: Optional[float] = 0
    statistics: Optional[float] = 0
    deep_learning: Optional[float] = 0


class DirectMatchRequest(BaseModel):
    student_name: Optional[str] = "Student"
    job_role: Optional[str] = "Job"
    student_skills: SkillProfile
    job_requirements: SkillProfile


def get_students():
    return pd.read_csv(os.path.join(DATA_DIR, "students.csv"))


def get_jobs():
    return pd.read_csv(os.path.join(DATA_DIR, "jobs.csv"))


@app.get("/")
def root():
    return {"message": "PlaceMux API is running", "status": "ok"}


@app.post("/match")
def match_student_to_job(req: MatchRequest):
    students = get_students()
    jobs = get_jobs()

    srow = students[students["student_id"] == req.student_id]
    jrow = jobs[jobs["job_id"] == req.job_id]

    if srow.empty:
        raise HTTPException(status_code=404, detail=f"Student {req.student_id} not found")
    if jrow.empty:
        raise HTTPException(status_code=404, detail=f"Job {req.job_id} not found")

    s_skills = srow[SKILL_COLS].iloc[0].to_dict()
    j_reqs = jrow[SKILL_COLS].iloc[0].to_dict()
    student_name = srow["name"].iloc[0]
    job_role = f"{jrow['role'].iloc[0]} @ {jrow['company'].iloc[0]}"

    result = generate_explanation(s_skills, j_reqs, student_name=student_name, job_role=job_role)
    result["student_id"] = req.student_id
    result["student_name"] = student_name
    result["job_id"] = req.job_id
    result["job_role"] = job_role
    return result


@app.post("/match/direct")
def match_direct(req: DirectMatchRequest):
    # useful for quick testing without needing IDs in the CSV
    s_skills = req.student_skills.dict()
    j_reqs = req.job_requirements.dict()
    return generate_explanation(s_skills, j_reqs, student_name=req.student_name, job_role=req.job_role)


@app.get("/students")
def list_students():
    return get_students().to_dict(orient="records")


@app.get("/students/{student_id}")
def get_student(student_id: int):
    df = get_students()
    row = df[df["student_id"] == student_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Student not found")
    return row.iloc[0].to_dict()


@app.get("/jobs")
def list_jobs():
    return get_jobs().to_dict(orient="records")


@app.get("/jobs/{job_id}")
def get_job(job_id: int):
    df = get_jobs()
    row = df[df["job_id"] == job_id]
    if row.empty:
        raise HTTPException(status_code=404, detail="Job not found")
    return row.iloc[0].to_dict()


@app.get("/jobs/{job_id}/rank")
def rank_students(job_id: int):
    df = rank_students_for_job(job_id)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return df.to_dict(orient="records")


@app.post("/validate")
def validate(req: MatchRequest):
    result = validate_by_id(req.student_id, req.job_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@app.post("/vectors")
def get_vectors(req: MatchRequest):
    result = compute_match_by_id(req.student_id, req.job_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
