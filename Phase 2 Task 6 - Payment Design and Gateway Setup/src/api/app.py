"""
app.py
------
FastAPI inference endpoint for PlaceMux matching.

Two endpoints:
  POST /match       → given a student + job, return a match score + reasons
  POST /rank_jobs   → given a student, rank a list of jobs by match quality
  GET  /health      → sanity check the service is up and the model loaded

Start server: uvicorn src.api.app:app --reload --port 8000
"""

import json
import os
import sys
from typing import List, Optional

import joblib
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

app = FastAPI(
    title="PlaceMux Matching API",
    description="Job-candidate matching with explainable scores",
    version="1.0.0",
)

# ── model + supporting data ───────────────────────────────────────────────────

MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../experiments/models/ranker_rf.joblib")

_model = None


def get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(
                f"Model file not found at {MODEL_PATH}. "
                "Run `python src/models/ranker.py` first."
            )
        _model = joblib.load(MODEL_PATH)
    return _model


FEATURE_COLS = [
    "skill_overlap_ratio",
    "mean_score_on_required",
    "score_gap_mean",
    "skills_below_threshold",
    "nice_to_have_overlap",
    "cgpa_gap",
    "max_skill_score",
    "avg_skill_score",
    "graduation_recency",
    "required_skills_count",
    "min_score_threshold",
]

ALL_SKILLS = [
    "Python", "SQL", "Machine Learning", "Deep Learning", "NLP",
    "Data Analysis", "Statistics", "Docker", "Git", "REST APIs",
    "Java", "JavaScript", "React", "Node.js", "Cloud (AWS/GCP/Azure)",
    "Spark", "Tableau", "Excel", "Communication", "Problem Solving",
]


# ── request / response schemas ────────────────────────────────────────────────

class StudentProfile(BaseModel):
    student_id: str
    skill_scores: dict = Field(
        description="skill_name → verified score (0–100)"
    )
    cgpa: float = Field(ge=0.0, le=10.0)
    graduation_year: int = Field(ge=2015, le=2030)


class JobDescription(BaseModel):
    job_id: str
    required_skills: List[str]
    nice_to_have_skills: List[str] = []
    min_score_threshold: int = Field(ge=0, le=100)
    min_cgpa: float = Field(ge=0.0, le=10.0)


class MatchRequest(BaseModel):
    student: StudentProfile
    job: JobDescription


class MatchResult(BaseModel):
    student_id: str
    job_id: str
    match_score: float = Field(description="0–1 probability of good match")
    match_label: int = Field(description="1 = match, 0 = no match")
    confidence: str
    reasons: List[str]


class RankRequest(BaseModel):
    student: StudentProfile
    jobs: List[JobDescription]
    top_k: int = Field(default=10, ge=1, le=50)


class RankedJob(BaseModel):
    rank: int
    job_id: str
    match_score: float
    reasons: List[str]


# ── feature computation ───────────────────────────────────────────────────────

def compute_features(student: StudentProfile, job: JobDescription) -> dict:
    scores = student.skill_scores

    req_scores = [scores.get(s, 0) for s in job.required_skills]
    threshold = job.min_score_threshold

    skill_overlap_ratio = (
        sum(1 for sc in req_scores if sc >= threshold) / len(req_scores)
        if req_scores else 0.0
    )
    mean_score_on_required = float(np.mean(req_scores)) if req_scores else 0.0
    score_gaps = [sc - threshold for sc in req_scores]
    score_gap_mean = float(np.mean(score_gaps)) if score_gaps else 0.0
    skills_below_threshold = sum(1 for g in score_gaps if g < 0)

    nice_scores = [scores.get(s, 0) for s in job.nice_to_have_skills]
    nice_overlap = (
        sum(1 for sc in nice_scores if sc >= 50) / len(nice_scores)
        if nice_scores else 0.0
    )

    all_scores = [scores.get(s, 0) for s in ALL_SKILLS]
    cgpa_gap = student.cgpa - job.min_cgpa
    recency = 2024 - student.graduation_year

    return {
        "skill_overlap_ratio": skill_overlap_ratio,
        "mean_score_on_required": mean_score_on_required,
        "score_gap_mean": score_gap_mean,
        "skills_below_threshold": skills_below_threshold,
        "nice_to_have_overlap": nice_overlap,
        "cgpa_gap": cgpa_gap,
        "max_skill_score": float(max(all_scores)) if all_scores else 0.0,
        "avg_skill_score": float(np.mean(all_scores)) if all_scores else 0.0,
        "graduation_recency": recency,
        "required_skills_count": len(job.required_skills),
        "min_score_threshold": threshold,
    }


def build_reasons(feats: dict, job: JobDescription, student: StudentProfile) -> list[str]:
    reasons = []
    overlap = feats["skill_overlap_ratio"]
    gap = feats["score_gap_mean"]
    below = int(feats["skills_below_threshold"])
    cgpa_gap = feats["cgpa_gap"]
    nice = feats["nice_to_have_overlap"]

    if overlap >= 0.8:
        reasons.append(f"Meets {overlap:.0%} of required skills (strong overlap)")
    elif overlap >= 0.5:
        reasons.append(f"Meets {overlap:.0%} of required skills (partial match)")
    else:
        reasons.append(f"Only meets {overlap:.0%} of required skills")

    if gap >= 0:
        reasons.append(f"Scores average {gap:+.1f} pts above the job threshold")
    else:
        reasons.append(f"Scores average {gap:.1f} pts below the job threshold")

    if below > 0:
        missing = [s for s in job.required_skills
                   if student.skill_scores.get(s, 0) < job.min_score_threshold]
        reasons.append(f"Missing/below threshold: {', '.join(missing[:3])}")
    else:
        reasons.append("All required skills meet the score threshold")

    if cgpa_gap >= 0.5:
        reasons.append(f"CGPA comfortably above the minimum (+{cgpa_gap:.1f})")
    elif cgpa_gap < 0:
        reasons.append(f"CGPA below job minimum by {abs(cgpa_gap):.1f}")

    if nice >= 0.5:
        reasons.append(f"Has {nice:.0%} of nice-to-have skills")

    return reasons


def score_to_confidence(score: float) -> str:
    if score >= 0.8:
        return "high"
    elif score >= 0.5:
        return "medium"
    else:
        return "low"


# ── endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    model_loaded = os.path.exists(MODEL_PATH)
    return {
        "status": "ok",
        "model_loaded": model_loaded,
        "model_path": MODEL_PATH,
    }


@app.post("/match", response_model=MatchResult)
def match(req: MatchRequest):
    model = get_model()
    feats = compute_features(req.student, req.job)
    X = np.array([[feats[col] for col in FEATURE_COLS]])

    proba = float(model.predict_proba(X)[0, 1])
    label = int(model.predict(X)[0])

    reasons = build_reasons(feats, req.job, req.student)

    return MatchResult(
        student_id=req.student.student_id,
        job_id=req.job.job_id,
        match_score=round(proba, 4),
        match_label=label,
        confidence=score_to_confidence(proba),
        reasons=reasons,
    )


@app.post("/rank_jobs", response_model=List[RankedJob])
def rank_jobs(req: RankRequest):
    model = get_model()
    scored = []

    for job in req.jobs:
        feats = compute_features(req.student, job)
        X = np.array([[feats[col] for col in FEATURE_COLS]])
        proba = float(model.predict_proba(X)[0, 1])
        reasons = build_reasons(feats, job, req.student)
        scored.append((job.job_id, proba, reasons))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        RankedJob(
            rank=i + 1,
            job_id=jid,
            match_score=round(score, 4),
            reasons=reasons,
        )
        for i, (jid, score, reasons) in enumerate(scored[: req.top_k])
    ]
