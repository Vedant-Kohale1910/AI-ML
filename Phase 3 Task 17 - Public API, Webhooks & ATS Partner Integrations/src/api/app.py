"""
app.py — FastAPI application exposing versioned ML endpoints.

Endpoints:
  POST /v1/score   — deprecated scoring (still live, sunset 2026-06-30)
  POST /v2/score   — production scoring endpoint
  POST /v2/match   — top-K matching for an ATS job posting
  GET  /v2/health  — health check
  GET  /docs       — auto-generated OpenAPI docs (partner documentation)

Authentication: API key via X-API-Key header.
  demo keys (for testing):
    partner-key-free       → free tier
    partner-key-standard   → partner tier
    partner-key-enterprise → enterprise tier
"""
import json
import os
import sys
from typing import Optional

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "../.."))

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from scoring.scoring_engine import score_match, MODEL_VERSIONS
from api.rate_limiter import check_and_record

# Partner API key registry
API_KEYS = {
    "partner-key-free":       "free",
    "partner-key-standard":   "partner",
    "partner-key-enterprise": "enterprise",
}

app = FastAPI(
    title="PlaceMux Intelligence API",
    description=(
        "Partner-facing API for AI-powered candidate-job matching and scoring.\n\n"
        "## Authentication\nPass your API key in the `X-API-Key` header.\n\n"
        "## Versioning\nEndpoints are URL-versioned. `/v1/` is deprecated (sunset 2026-06-30). "
        "Use `/v2/` for production integrations.\n\n"
        "## Rate limits\n"
        "| Tier | Requests/day | Requests/min |\n|---|---|---|\n"
        "| Free | 100 | 10 |\n| Partner | 5,000 | 100 |\n| Enterprise | Unlimited | 500 |\n\n"
        "## What is never returned\nRaw model weights, internal feature scores, "
        "or other partners' candidate data."
    ),
    version="2.0",
)


# ── Pydantic models ──────────────────────────────────────────────────────────

class ScoreRequest(BaseModel):
    candidate: dict
    job: dict
    class Config:
        json_schema_extra = {
            "example": {
                "candidate": {
                    "student_id": 1, "name": "Aarav Patel",
                    "verified_skills": ["Python","Machine Learning","SQL"],
                    "years_experience": 3, "assessment_score": 0.89,
                    "certifications": []
                },
                "job": {
                    "job_id": 1, "title": "ML Engineer",
                    "required_skills": ["Python","Machine Learning"],
                    "required_experience_years": 2,
                    "preferred_certifications": []
                }
            }
        }

class MatchRequest(BaseModel):
    job: dict
    candidates: list
    top_k: Optional[int] = 5


# ── Auth + quota helper ──────────────────────────────────────────────────────

def _auth_and_quota(x_api_key: str, candidate_id=None, job_id=None):
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")
    tier   = API_KEYS[x_api_key]
    result = check_and_record(x_api_key, tier, candidate_id, job_id)
    if not result["allowed"]:
        raise HTTPException(status_code=429, detail=result["reason"])
    return tier, result


# ── v2 endpoints (production) ─────────────────────────────────────────────────

@app.post("/v2/score", tags=["v2 - Production"],
          summary="Score a candidate against a job posting",
          response_description="Match decision, confidence band and plain-English explanation")
def v2_score(req: ScoreRequest, x_api_key: str = Header(...)):
    tier, quota = _auth_and_quota(
        x_api_key,
        req.candidate.get("student_id"),
        req.job.get("job_id")
    )
    result = score_match(req.candidate, req.job, api_version="v2")
    result["quota_remaining_day"] = quota["remaining_day"]
    return result


@app.post("/v2/match", tags=["v2 - Production"],
          summary="Return top-K matching candidates for a job (ATS integration)")
def v2_match(req: MatchRequest, x_api_key: str = Header(...)):
    tier, quota = _auth_and_quota(x_api_key)
    results = []
    for candidate in req.candidates:
        r = score_match(candidate, req.job, api_version="v2")
        if r["match"]:
            results.append(r)
    results.sort(key=lambda x: x["confidence_band"])  # HIGH → MEDIUM → LOW
    return {
        "job_id":      req.job.get("job_id"),
        "job_title":   req.job.get("title"),
        "model_id":    MODEL_VERSIONS["v2"]["model_id"],
        "top_k":       req.top_k,
        "matches":     results[:req.top_k],
        "total_evaluated": len(req.candidates),
        "quota_remaining_day": quota["remaining_day"],
    }


@app.get("/v2/health", tags=["v2 - Production"])
def v2_health():
    return {"status": "ok", "model_id": MODEL_VERSIONS["v2"]["model_id"],
            "api_version": "v2"}


# ── v1 endpoint (deprecated) ──────────────────────────────────────────────────

@app.post("/v1/score", tags=["v1 - Deprecated (sunset 2026-06-30)"],
          summary="[DEPRECATED] Score endpoint — migrate to /v2/score")
def v1_score(req: ScoreRequest, x_api_key: str = Header(...)):
    tier, quota = _auth_and_quota(x_api_key)
    result = score_match(req.candidate, req.job, api_version="v1")
    result["migration_notice"] = (
        "This endpoint is deprecated and will be removed on 2026-06-30. "
        "Please migrate to /v2/score. Behaviour differences: v2 uses improved "
        "skill weights (0.55 vs 0.40) and a stricter threshold (0.40 vs 0.35)."
    )
    return result
