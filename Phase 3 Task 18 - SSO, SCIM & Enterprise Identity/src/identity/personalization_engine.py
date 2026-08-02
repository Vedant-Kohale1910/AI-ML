"""
personalization_engine.py — Identity-aware recommendation scoring.

Blends three signal layers:
  1. Recruiter signals (current org only) — highest weight
  2. Org signals — medium weight
  3. Global baseline (feature score from Phase-2 engine) — fallback floor

Fallback: if personalization service is disabled, returns pure feature score.
"""
import sys
import os

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "../.."))

from recommendation.feature_engineering import FeatureEngineer
from identity.signal_manager import (get_recruiter_signals, get_org_signals,
                                      get_identity)

_fe = FeatureEngineer()
_enabled = True   # toggle for failure scenario


def set_enabled(state: bool):
    global _enabled
    _enabled = state


def _skill_boost(signals: list, student_skills: list) -> float:
    """Compute boost from signals: how many shortlisted candidates share skills."""
    if not signals:
        return 0.0
    shortlisted_skills = set()
    for s in signals:
        if s["type"] in ("shortlist", "apply") and s.get("skill"):
            shortlisted_skills.add(s["skill"].lower())
    student_skill_set = set(sk.lower() for sk in student_skills)
    overlap = len(shortlisted_skills & student_skill_set)
    return min(0.20, overlap * 0.05)   # max +0.20 boost


def personalized_score(recruiter_id: str, student: dict, job: dict) -> dict:
    """
    Score one student for one job using recruiter + org signals.
    Falls back to pure feature score if personalization is disabled.
    """
    feats = _fe.extract_features(student, job)
    base_score = round(
        0.55 * feats.get("skill_match", 0) +
        0.25 * feats.get("experience_match", 0) +
        0.10 * feats.get("assessment_score", 0) +
        0.10 * feats.get("certification_match", 0), 4)

    if not _enabled:
        return {"score": base_score, "source": "fallback_feature_only",
                "personalization": "disabled"}

    identity = get_identity(recruiter_id)
    org_id   = identity["org_id"]

    rec_sigs = get_recruiter_signals(recruiter_id)
    org_sigs = get_org_signals(org_id)

    student_skills = student.get("verified_skills", [])
    rec_boost  = _skill_boost(rec_sigs, student_skills)
    org_boost  = _skill_boost(org_sigs, student_skills) * 0.5

    final = round(min(1.0, base_score + rec_boost + org_boost), 4)
    return {
        "score":           final,
        "base_score":      base_score,
        "recruiter_boost": round(rec_boost, 4),
        "org_boost":       round(org_boost, 4),
        "recruiter_signals": len(rec_sigs),
        "org_signals":       len(org_sigs),
        "org_scope":         org_id,
        "source":            "personalized",
    }


def recommend(recruiter_id: str, students: list, job: dict, top_k: int = 5) -> list:
    results = []
    for student in students:
        r = personalized_score(recruiter_id, student, job)
        results.append({
            "student_id":   student["student_id"],
            "name":         student["name"],
            "skills":       student["verified_skills"],
            **r,
        })
    results.sort(key=lambda x: -x["score"])
    return results[:top_k]
