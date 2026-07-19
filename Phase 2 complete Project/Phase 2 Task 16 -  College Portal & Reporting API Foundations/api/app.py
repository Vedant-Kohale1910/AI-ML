"""
FastAPI application for Recommendation Engine v1
Serves recommendations via REST API
"""

# -- utf8-console-guard --
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
import os
import logging


def _to_native(obj):
    """Recursively convert numpy scalars/arrays to plain Python types so
    pydantic/JSON can serialize them (numpy.int64 is not JSON-serializable)."""
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(v) for v in obj]
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return [_to_native(v) for v in obj.tolist()]
    return obj
from pathlib import Path

# Add parent directory to path to import recommendation module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from recommendation.recommender import RecommendationEngine

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="PlaceMux Recommendation Engine v1",
    description="AI-powered job recommendation system for college placements",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load data and initialize engine
DATA_DIR = Path(__file__).parent.parent / "data"

try:
    students_df = pd.read_csv(DATA_DIR / "students.csv")
    jobs_df = pd.read_csv(DATA_DIR / "jobs.csv")
    recommendation_engine = RecommendationEngine(students_df, jobs_df)
    logger.info(f"Loaded {len(students_df)} students and {len(jobs_df)} jobs")
except Exception as e:
    logger.error(f"Failed to load data: {e}")
    recommendation_engine = None


# Pydantic models for API
class ScoreBreakdown(BaseModel):
    skill_match: float
    assessment: float
    experience: float
    certification: float
    education: float


class RecommendedJob(BaseModel):
    rank: int
    job_id: int
    job_title: str
    overall_score: float
    score_breakdown: ScoreBreakdown
    explanation: str
    reasoning: Dict[str, str]


class RecommendationResponse(BaseModel):
    student_id: int
    student_name: str
    student_profile: Dict
    top_recommendations: List[RecommendedJob]
    scoring_weights: Dict[str, float]


class HealthResponse(BaseModel):
    status: str
    engine_ready: bool
    students_loaded: int
    jobs_loaded: int


# API Endpoints

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint
    Verifies that the recommendation engine is loaded and ready
    """
    return {
        "status": "healthy",
        "engine_ready": recommendation_engine is not None,
        "students_loaded": len(students_df) if recommendation_engine else 0,
        "jobs_loaded": len(jobs_df) if recommendation_engine else 0
    }


@app.get("/api/v1/recommend/{student_id}", response_model=RecommendationResponse)
async def get_recommendations(
    student_id: int,
    top_n: int = Query(5, ge=1, le=10, description="Number of top recommendations")
):
    """
    Get job recommendations for a student
    
    Args:
        student_id: ID of the student
        top_n: Number of top recommendations (1-10, default 5)
    
    Returns:
        RecommendationResponse with top N recommendations and explanations
    
    Example:
        GET /api/v1/recommend/1?top_n=5
    """
    if recommendation_engine is None:
        raise HTTPException(
            status_code=503,
            detail="Recommendation engine not initialized"
        )
    
    try:
        report = _to_native(recommendation_engine.get_recommendation_report(student_id, top_n))

        if not report['top_recommendations']:
            raise HTTPException(
                status_code=404,
                detail=f"Student {student_id} not found or no recommendations available"
            )
        
        return RecommendationResponse(**report)

    except HTTPException:
        raise  # let 404/503 through untouched instead of masking them as 500
    except Exception as e:
        logger.error(f"Error generating recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/students")
async def list_students(skip: int = 0, limit: int = 10):
    """
    List all students in the system
    
    Args:
        skip: Number of students to skip (pagination)
        limit: Maximum number of students to return
    
    Returns:
        List of students with basic info
    """
    if recommendation_engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    try:
        students_list = []
        for _, student in students_df.iterrows():
            students_list.append({
                "student_id": int(student['student_id']),
                "name": student['name'],
                "verified_skills": student['verified_skills'],
                "assessment_score": int(student['assessment_score']),
                "experience_years": float(student['years_experience'])
            })
        
        return {
            "total": len(students_list),
            "students": students_list[skip:skip+limit]
        }
    except Exception as e:
        logger.error(f"Error listing students: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/jobs")
async def list_jobs(skip: int = 0, limit: int = 10):
    """
    List all jobs in the system
    
    Args:
        skip: Number of jobs to skip (pagination)
        limit: Maximum number of jobs to return
    
    Returns:
        List of jobs with requirements
    """
    if recommendation_engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    try:
        jobs_list = []
        for _, job in jobs_df.iterrows():
            jobs_list.append({
                "job_id": int(job['job_id']),
                "title": job['title'],
                "company": job['company'],
                "required_skills": job['required_skills'],
                "required_experience": float(job['required_experience'])
            })
        
        return {
            "total": len(jobs_list),
            "jobs": jobs_list[skip:skip+limit]
        }
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/info")
async def get_engine_info():
    """
    Get information about the recommendation engine
    
    Returns:
        Information about scoring weights and methodology
    """
    if recommendation_engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    return {
        "engine": "Recommendation v1",
        "version": "1.0.0",
        "methodology": "Multi-factor weighted recommendation",
        "scoring_weights": recommendation_engine.WEIGHTS,
        "scoring_formula": (
            "Overall Score = 0.50 × Skill Match + 0.20 × Assessment Score "
            "+ 0.15 × Experience Match + 0.10 × Certification Match + 0.05 × Education Match"
        ),
        "features_considered": [
            "Verified skills match",
            "Assessment score (normalized 0-1)",
            "Years of experience vs requirement",
            "Relevant certifications",
            "Education level"
        ],
        "explanation": "Each recommendation includes plain-English explanation of why the job is recommended"
    }


@app.get("/api/v1/student/{student_id}")
async def get_student_profile(student_id: int):
    """
    Get detailed profile of a specific student
    
    Args:
        student_id: ID of the student
    
    Returns:
        Complete student profile
    """
    if recommendation_engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    try:
        student = students_df[students_df['student_id'] == student_id]
        if student.empty:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
        
        student = student.iloc[0]
        return {
            "student_id": int(student['student_id']),
            "name": student['name'],
            "verified_skills": student['verified_skills'],
            "years_experience": float(student['years_experience']),
            "assessment_score": int(student['assessment_score']),
            "certifications": student['certifications'],
            "education_level": student['education_level']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting student profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/job/{job_id}")
async def get_job_details(job_id: int):
    """
    Get detailed information about a specific job
    
    Args:
        job_id: ID of the job
    
    Returns:
        Complete job details
    """
    if recommendation_engine is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    
    try:
        job = jobs_df[jobs_df['job_id'] == job_id]
        if job.empty:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        job = job.iloc[0]
        return {
            "job_id": int(job['job_id']),
            "title": job['title'],
            "company": job['company'],
            "required_skills": job['required_skills'],
            "required_experience": float(job['required_experience']),
            "preferred_certifications": job['preferred_certifications'],
            "education_requirement": job['education_requirement']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job details: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with API documentation"""
    return {
        "name": "PlaceMux Recommendation Engine v1",
        "version": "1.0.0",
        "description": "AI-powered job recommendation system for college placements",
        "endpoints": {
            "health": "GET /health - Health check",
            "recommend": "GET /api/v1/recommend/{student_id} - Get recommendations for a student",
            "students": "GET /api/v1/students - List all students",
            "jobs": "GET /api/v1/jobs - List all jobs",
            "info": "GET /api/v1/info - Get engine information",
            "student_profile": "GET /api/v1/student/{student_id} - Get student profile",
            "job_details": "GET /api/v1/job/{job_id} - Get job details"
        },
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
