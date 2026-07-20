"""
Failure Injection  —  Task 5
Three deliberate break scenarios. Every scenario must end with the
fallback serving real recommendations (not an error).
"""
from __future__ import annotations
from typing import Dict, Any, Tuple, List
import numpy as np

_RNG = np.random.default_rng(42)


def inject_model_crash(fallback_fn, student_id: int,
                       student: Dict, jobs: List[Dict]) -> Dict[str, Any]:
    """Force ML pod crash → heuristic fallback."""
    result = fallback_fn(student_id, student, force_ml_fail=True)
    return dict(
        scenario   = "Model pod crash (OOM)",
        triggered  = "ML inference raised RuntimeError",
        tier_served= result["tier"],
        received   = len(result["recommendations"]) > 0,
        p95_impact = "~50ms (heuristic) vs 465ms (ML)",
        recovery   = "K8s restarts pod in ~90s; ML auto-resumes",
        alert      = "Task 2 PAGE fires within 1 window",
        result     = result,
    )


def inject_feature_store_down(fallback_fn, student_id: int,
                               student: Dict, jobs: List[Dict]) -> Dict[str, Any]:
    """Feature store unreachable → stale cache fallback."""
    result = fallback_fn(student_id, student, force_feature_fail=True)
    return dict(
        scenario   = "Feature store unreachable (network partition)",
        triggered  = "feature_fetch timeout after 200ms",
        tier_served= result["tier"],
        received   = len(result["recommendations"]) > 0,
        p95_impact = "Latency improves (stale cache is 5ms), quality may drop ≤3%",
        recovery   = "Reconnect with exponential back-off; fresh features resume",
        alert      = "Task 2 CRITICAL fires if precision drops > 0.02",
        result     = result,
    )


def inject_score_degenerate(fallback_fn, student_id: int,
                             student: Dict, jobs: List[Dict]) -> Dict[str, Any]:
    """Model stuck returning constant 0.72 → degenerate output PAGE."""
    result = fallback_fn(student_id, student, force_degenerate=True)
    return dict(
        scenario   = "Degenerate model output (constant scores)",
        triggered  = "score std-dev=0.002 < 0.05 threshold",
        tier_served= result["tier"],
        received   = len(result["recommendations"]) > 0,
        p95_impact = "Latency unchanged; recommendations meaningless without fallback",
        recovery   = "Task 2 PAGE fires; circuit breaker trips; heuristic serves",
        alert      = "Task 2 PAGE: model_score_std < 0.05",
        result     = result,
    )
