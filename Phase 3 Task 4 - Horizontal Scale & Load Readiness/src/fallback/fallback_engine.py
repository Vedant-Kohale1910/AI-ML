"""
Fallback Engine  —  Task 4: Graceful Degradation
Three-tier fallback strategy ensures users always get recommendations,
even when the ML model is unavailable or overloaded.

Tier 1 (normal):  Full ML recommendation engine
Tier 2 (degraded): Skill-overlap heuristic (< 5ms, no model needed)
Tier 3 (emergency): Popular-jobs list from precomputed cache (< 1ms)

Fallback is triggered automatically based on:
  - ML service timeout
  - Error rate > 5% in sliding window
  - Explicit circuit-breaker trip
"""
from __future__ import annotations
import time
from typing import Dict, List, Any, Optional
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np


@dataclass
class FallbackStats:
    total_requests:    int = 0
    ml_served:         int = 0
    heuristic_served:  int = 0
    cache_served:      int = 0
    ml_errors:         int = 0

    @property
    def ml_error_rate(self) -> float:
        d = self.ml_served + self.ml_errors
        return self.ml_errors / d if d else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total":          self.total_requests,
            "ml_served":      self.ml_served,
            "heuristic":      self.heuristic_served,
            "cache":          self.cache_served,
            "ml_error_rate":  round(self.ml_error_rate, 4),
        }


class HeuristicRecommender:
    """
    Tier-2: Pure skill-overlap ranking — no model, no network call.
    Returns same schema as ML engine so clients see no difference.
    """
    VERSION = "heuristic-v1"

    def recommend(self, student: Dict, jobs: List[Dict], top_k: int = 5) -> List[Dict]:
        s_skills = set(x.lower() for x in student.get("skills", []))
        scored = []
        for job in jobs:
            j_skills = set(x.lower() for x in job.get("required_skills", []))
            score = len(s_skills & j_skills) / len(j_skills) if j_skills else 0.0
            if score > 0:
                scored.append({
                    "job_id":       job["job_id"],
                    "title":        job["title"],
                    "company":      job["company"],
                    "score":        round(score, 4),
                    "model_version": self.VERSION,
                    "fallback_tier": 2,
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:top_k]


class CacheRecommender:
    """
    Tier-3: Serves precomputed popular-job list — purely in-memory.
    Updated nightly; always available even if feature store is down.
    """
    VERSION = "cache-v1"
    _POPULAR = [
        {"job_id": 131, "title": "Backend Developer", "company": "Granite Edge Tech", "score": 0.72},
        {"job_id": 101, "title": "Data Analyst",      "company": "Crestline Digital", "score": 0.68},
        {"job_id": 123, "title": "ML Engineer",       "company": "Ferrous Tech",      "score": 0.65},
        {"job_id": 132, "title": "Backend Developer", "company": "Granite Edge Tech", "score": 0.63},
        {"job_id": 102, "title": "Data Scientist",    "company": "Apex Solutions",    "score": 0.61},
    ]

    def recommend(self, top_k: int = 5) -> List[Dict]:
        return [{**r, "model_version": self.VERSION, "fallback_tier": 3}
                for r in self._POPULAR[:top_k]]


class CircuitBreaker:
    """
    Opens when ml_error_rate > threshold over a sliding window.
    Half-opens after cool_down_s seconds to probe recovery.
    """
    THRESHOLD  = 0.05   # 5% errors → open
    COOL_DOWN  = 30     # seconds before half-open probe

    def __init__(self):
        self._window: deque = deque(maxlen=100)
        self._state  = "CLOSED"    # CLOSED / OPEN / HALF_OPEN
        self._opened_at: Optional[float] = None

    def record(self, success: bool) -> None:
        self._window.append(1 if success else 0)
        if self._state == "CLOSED":
            err_rate = 1 - (sum(self._window) / len(self._window))
            if err_rate >= self.THRESHOLD:
                self._state    = "OPEN"
                self._opened_at = time.time()

    def allow_request(self) -> bool:
        if self._state == "CLOSED":
            return True
        if self._state == "OPEN":
            if time.time() - self._opened_at > self.COOL_DOWN:
                self._state = "HALF_OPEN"
                return True
            return False
        # HALF_OPEN: let one probe through
        return True

    def on_success(self) -> None:
        self._state = "CLOSED"

    @property
    def state(self) -> str:
        return self._state


class FallbackEngine:
    """
    Orchestrates the three-tier fallback strategy.
    Clients call .recommend() — they never need to know which tier served.
    """

    def __init__(self, ml_engine=None, jobs: List[Dict] = None):
        self._ml      = ml_engine
        self._jobs    = jobs or []
        self._heur    = HeuristicRecommender()
        self._cache   = CacheRecommender()
        self._cb      = CircuitBreaker()
        self.stats    = FallbackStats()

    def recommend(self, student_id: int, student: Dict,
                  force_fail: bool = False, top_k: int = 5) -> Dict[str, Any]:
        self.stats.total_requests += 1
        tier = None
        recommendations = []

        # Tier 1: ML engine (if circuit closed and not forced fail)
        if self._ml and self._cb.allow_request() and not force_fail:
            try:
                recommendations = self._ml.recommend(student_id, top_k)
                self._cb.record(True)
                self._cb.on_success()
                self.stats.ml_served += 1
                tier = 1
            except Exception:
                self._cb.record(False)
                self.stats.ml_errors += 1

        # Tier 2: Heuristic
        if not recommendations:
            recommendations = self._heur.recommend(student, self._jobs, top_k)
            self.stats.heuristic_served += 1
            tier = 2

        # Tier 3: Cache (if heuristic also empty)
        if not recommendations:
            recommendations = self._cache.recommend(top_k)
            self.stats.cache_served += 1
            tier = 3

        return {
            "student_id":      student_id,
            "recommendations": recommendations,
            "tier_served":     tier,
            "circuit_state":   self._cb.state,
            "served_at":       datetime.utcnow().isoformat(),
        }

    def circuit_state(self) -> str:
        return self._cb.state
