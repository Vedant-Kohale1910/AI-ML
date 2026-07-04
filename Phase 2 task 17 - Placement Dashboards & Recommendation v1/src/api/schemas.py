"""
API Schemas
Pydantic models for request/response validation
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class RecommendationRequest(BaseModel):
    """Request to get recommendations for a student."""
    student_id: int = Field(..., description="Student ID")
    top_k: int = Field(5, ge=1, le=20, description="Number of recommendations to return")


class ExplainRequest(BaseModel):
    """Request to explain a specific recommendation."""
    student_id: int = Field(..., description="Student ID")
    job_id: int = Field(..., description="Job ID")


class SkillAnalysis(BaseModel):
    """Skill analysis breakdown."""
    matched: List[str]
    missing: List[str]
    coverage: str


class ExperienceAnalysis(BaseModel):
    """Experience analysis breakdown."""
    student_years: int
    required_years: int
    status: str
    gap: int


class ExplanationDetail(BaseModel):
    """Detailed explanation for a recommendation."""
    score: float
    recommendation_level: str
    skill_analysis: Dict[str, Any]
    experience_analysis: Dict[str, Any]
    assessment_analysis: Dict[str, Any]
    certification_analysis: Dict[str, Any]
    education_analysis: Dict[str, Any]
    summary: str


class RecommendedJob(BaseModel):
    """A recommended job."""
    job_id: int
    title: str
    company: str
    score: float
    rank: int
    explanation: Optional[Dict[str, Any]] = None


class RecommendationResponse(BaseModel):
    """Response with recommendations."""
    student_id: int
    student_name: Optional[str] = None
    recommended_jobs: List[RecommendedJob]
    total_jobs_evaluated: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExplainResponse(BaseModel):
    """Response with detailed explanation."""
    student_id: int
    job_id: int
    job_title: str
    score: float
    explanation: ExplanationDetail


class MetricsResponse(BaseModel):
    """Response with system metrics."""
    baseline_accuracy: float
    recommendation_v1_accuracy: float
    precision: float
    recall: float
    false_positive_rate: float
    improvement_over_baseline: float
    sample_size: int
    evaluation_date: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    students_loaded: int
    jobs_loaded: int
    recommendations_available: bool


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: str
    status_code: int
