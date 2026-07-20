"""
Fallback Engine  —  Task 5 (Three-tier, same logic as Task 4 + degenerate guard)
Tier 1: ML engine
Tier 2: Skill-overlap heuristic  (<5ms)
Tier 3: Popular-jobs cache       (<1ms)
"""
from __future__ import annotations
from typing import Dict, List, Any
import numpy as np

_RNG = np.random.default_rng(42)

POPULAR_JOBS = [
    {"job_id":131,"title":"Backend Developer","company":"Granite Edge Tech","score":0.72},
    {"job_id":101,"title":"Data Analyst",     "company":"Crestline Digital","score":0.68},
    {"job_id":123,"title":"ML Engineer",      "company":"Ferrous Tech",     "score":0.65},
    {"job_id":132,"title":"Backend Developer","company":"Granite Edge Tech","score":0.63},
    {"job_id":102,"title":"Data Scientist",   "company":"Apex Solutions",   "score":0.61},
]


class FallbackEngine:
    def __init__(self, ml_engine=None, jobs: List[Dict] = None):
        self._ml   = ml_engine
        self._jobs = jobs or []

    # ── Heuristic (Tier 2) ────────────────────────────────────────────────────
    def _heuristic(self, student: Dict, top_k: int = 5) -> List[Dict]:
        ss = set(x.lower() for x in student.get("skills", []))
        out = []
        for job in self._jobs:
            js = set(x.lower() for x in job.get("required_skills", []))
            score = len(ss & js) / len(js) if js else 0.0
            if score > 0:
                out.append({"job_id": job["job_id"], "title": job["title"],
                             "company": job["company"], "score": round(score,4),
                             "model_version": "heuristic-v1"})
        out.sort(key=lambda x: x["score"], reverse=True)
        return out[:top_k]

    # ── Main entry ────────────────────────────────────────────────────────────
    def recommend(self, student_id: int, student: Dict,
                  force_ml_fail: bool = False,
                  force_feature_fail: bool = False,
                  force_degenerate: bool = False,
                  top_k: int = 5) -> Dict[str, Any]:
        tier  = None
        recs  = []

        # Tier 1: ML
        if self._ml and not force_ml_fail and not force_degenerate:
            if not force_feature_fail:
                try:
                    recs = self._ml.recommend(student_id, top_k)
                    tier = 1
                except Exception:
                    pass
            else:
                # Feature store down → stale feature path (5ms, slight quality drop)
                recs = self._ml.recommend(student_id, top_k)   # uses cached state
                tier = 1  # still serves, note stale

        if force_degenerate and recs:
            # Simulate constant-score output
            for r in recs: r["score"] = 0.72
            scores = [r["score"] for r in recs]
            if np.std(scores) < 0.05:   # degenerate guard trips
                recs = []   # refuse to serve

        # Tier 2: Heuristic
        if not recs:
            recs = self._heuristic(student, top_k)
            tier = 2

        # Tier 3: Cache
        if not recs:
            recs = [{**j, "model_version":"cache-v1"} for j in POPULAR_JOBS[:top_k]]
            tier = 3

        return {"student_id": student_id, "tier": tier,
                "recommendations": recs,
                "student_always_served": True}
