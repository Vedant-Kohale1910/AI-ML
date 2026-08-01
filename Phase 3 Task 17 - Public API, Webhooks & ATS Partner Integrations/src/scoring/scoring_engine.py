"""
scoring_engine.py — Versioned scoring/matching with explanations.

API versioning decision: URL-versioned (/v1/, /v2/) over header versioning.
  Partners pin to a URL version. A model upgrade creates a new URL version.
  Old versions stay live for 6 months. Partners are notified before sunset.
  Rejected: Accept-version header — invisible to partners, breaks caching,
  hard to test without custom headers.

What we NEVER expose to partners:
  - Raw feature weights (model extraction risk)
  - Internal candidate scores from other partners
  - Training data or gradients
What we DO expose:
  - Bucketed confidence band (HIGH/MEDIUM/LOW) — not raw float
  - Plain-English explanation (skill/exp/cert reasons)
  - Model version string
"""
import json
import os
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "../.."))

from recommendation.feature_engineering import FeatureEngineer

MODEL_VERSIONS = {
    "v1": {
        "model_id":      "reco-v1.0",
        "weights":       {"skill": 0.40, "exp": 0.30, "assess": 0.20, "cert": 0.10},
        "threshold":     0.35,
        "sunset_date":   "2026-06-30",
        "status":        "deprecated",
    },
    "v2": {
        "model_id":      "reco-v2.0",
        "weights":       {"skill": 0.55, "exp": 0.25, "assess": 0.10, "cert": 0.10},
        "threshold":     0.40,
        "sunset_date":   None,
        "status":        "production",
    },
}
_fe = FeatureEngineer()


def _confidence_band(score: float) -> str:
    """Return bucketed band. Never expose raw float to partners."""
    if score >= 0.75: return "HIGH"
    if score >= 0.45: return "MEDIUM"
    return "LOW"


def score_match(candidate: dict, job: dict, api_version: str = "v2") -> dict:
    """
    Core scoring function used by all API endpoints.
    Returns structured response safe for external partners.
    """
    if api_version not in MODEL_VERSIONS:
        raise ValueError(f"Unknown API version '{api_version}'. Use: {list(MODEL_VERSIONS)}")

    cfg    = MODEL_VERSIONS[api_version]
    feats  = _fe.extract_features(candidate, job)
    w      = cfg["weights"]
    score  = round(
        w["skill"]  * feats.get("skill_match", 0) +
        w["exp"]    * feats.get("experience_match", 0) +
        w["assess"] * feats.get("assessment_score", 0) +
        w["cert"]   * feats.get("certification_match", 0), 4)

    matched = sorted(set(s.lower() for s in candidate.get("verified_skills", []))
                     & set(s.lower() for s in job.get("required_skills", [])))
    missing = sorted(set(s.lower() for s in job.get("required_skills", []))
                     - set(s.lower() for s in candidate.get("verified_skills", [])))
    exp_gap = candidate.get("years_experience", 0) - job.get("required_experience_years", 0)

    reasons = []
    if matched:
        reasons.append(f"Required skills matched: {', '.join(matched)}")
    if exp_gap >= 0:
        reasons.append(f"Experience satisfied ({candidate['years_experience']} yrs ≥ {job['required_experience_years']} required)")
    elif missing:
        reasons.append(f"Skills to develop: {', '.join(missing[:3])}")

    return {
        "api_version":       api_version,
        "model_id":          cfg["model_id"],
        "candidate_id":      candidate["student_id"],
        "job_id":            job["job_id"],
        "match":             score >= cfg["threshold"],
        "confidence_band":   _confidence_band(score),  # bucketed — no raw score exposed
        "explanation":       reasons if reasons else ["Partial skill overlap"],
        "proxy_risk_note":   "Score uses skills, experience, certifications only. Protected attributes not used.",
        "deprecated":        cfg["status"] == "deprecated",
        "migration_notice":  "Migrate to /v2/score by 2026-06-30. v2 uses improved weights (skill 0.55 vs 0.40) and stricter threshold." if cfg["status"] == "deprecated" else None,
        "sunset_date":       cfg["sunset_date"],
        "request_id":        f"REQ-{int(time.time()*1000) % 1000000:06d}",
    }
