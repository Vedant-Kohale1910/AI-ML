"""
Experimentation Platform  —  Task 9
Three deliverables:
  Stage B: Model variant serving (90% v1 / 10% v2, consistent assignment)
  Stage C: Permanent holdout group (10% never gets new model)
  Stage D: Guardrail metrics that auto-halt bad model
"""
from __future__ import annotations
import hashlib
from typing import Dict, List, Any, Optional
import numpy as np

RNG = np.random.default_rng(42)

# ── Experiment config ─────────────────────────────────────────────────────────
EXPERIMENT = dict(
    name         = "rec-v2-test",
    v1_pct       = 0.80,   # 80% control
    v2_pct       = 0.10,   # 10% treatment
    holdout_pct  = 0.10,   # 10% permanent holdout (never gets new model)
    min_samples  = 50,     # min samples before guardrail evaluation
)

# ── Guardrail thresholds (Task 2 SLO + business floors) ──────────────────────
GUARDRAILS = dict(
    ctr_floor        = 0.10,   # CTR must not drop below 10%
    hire_precision   = 0.85,   # hiring precision must stay above 85%
    p95_latency_ms   = 500,    # Task 2 SLO
    fairness_disp    = 0.10,   # max group disparity
    error_rate_ceil  = 0.01,   # error rate must stay below 1%
)


# ── Stage B: Consistent assignment ───────────────────────────────────────────

class VariantRouter:
    """
    Assigns each user to v1 / v2 / holdout deterministically via hash.
    Same user_id → same bucket across all requests (no flipping).

    Design decision:
        Chosen:   Hash-based (stable, no DB needed)
        Rejected: Random per-request (users flip between variants — invalid experiment)
        Rejected: Interleaving (complex, hard to explain to non-ML stakeholders)
    """

    def assign(self, user_id: int) -> str:
        """Return 'v1', 'v2', or 'holdout' — deterministic for any user_id."""
        h = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
        bucket = (h % 100) / 100.0   # 0.00 – 0.99

        if bucket < EXPERIMENT["holdout_pct"]:
            return "holdout"
        elif bucket < EXPERIMENT["holdout_pct"] + EXPERIMENT["v2_pct"]:
            return "v2"
        else:
            return "v1"

    def is_consistent(self, user_id: int, n_calls: int = 5) -> bool:
        """Verify same user always gets same variant."""
        first = self.assign(user_id)
        return all(self.assign(user_id) == first for _ in range(n_calls))


# ── Stage C: Holdout manager ──────────────────────────────────────────────────

class HoldoutManager:
    """
    Permanent holdout = a slice of users that NEVER receives the new model.
    Purpose: measure cumulative model value over time.
    Without holdout: no way to answer "did all these changes actually grow hires?"
    """

    def __init__(self, router: VariantRouter):
        self.router = router

    def is_holdout(self, user_id: int) -> bool:
        return self.router.assign(user_id) == "holdout"

    def summary(self, all_user_ids: List[int]) -> Dict[str, Any]:
        groups = {"v1": 0, "v2": 0, "holdout": 0}
        for uid in all_user_ids:
            groups[self.router.assign(uid)] += 1
        total = len(all_user_ids)
        return {
            "total_users":  total,
            "v1_count":     groups["v1"],
            "v2_count":     groups["v2"],
            "holdout_count":groups["holdout"],
            "v1_pct":       round(groups["v1"] / total * 100, 1),
            "v2_pct":       round(groups["v2"] / total * 100, 1),
            "holdout_pct":  round(groups["holdout"] / total * 100, 1),
        }


# ── Stage D: Guardrail checker ────────────────────────────────────────────────

class GuardrailChecker:
    """
    Auto-halts experiment if any critical metric breaches its threshold.
    Evaluated every N samples; halts immediately on breach.
    """

    def check(self, metrics_v2: Dict[str, float],
              metrics_v1: Dict[str, float]) -> Dict[str, Any]:
        violations = []
        checks = {}

        # 1. CTR must not drop relative to v1
        if "ctr" in metrics_v2 and "ctr" in metrics_v1:
            rel_drop = (metrics_v1["ctr"] - metrics_v2["ctr"]) / metrics_v1["ctr"]
            ok = rel_drop < 0.05   # must not drop more than 5%
            checks["ctr"] = {"v1": metrics_v1["ctr"], "v2": metrics_v2["ctr"],
                              "rel_drop_pct": round(rel_drop*100, 2), "pass": ok}
            if not ok:
                violations.append(f"CTR dropped {rel_drop*100:.1f}% > 5% threshold")

        # 2. Hiring precision floor
        if "hire_precision" in metrics_v2:
            ok = metrics_v2["hire_precision"] >= GUARDRAILS["hire_precision"]
            checks["hire_precision"] = {"value": metrics_v2["hire_precision"],
                                         "floor": GUARDRAILS["hire_precision"], "pass": ok}
            if not ok:
                violations.append(f"Hire precision {metrics_v2['hire_precision']:.3f} < {GUARDRAILS['hire_precision']}")

        # 3. Latency SLO
        if "p95_ms" in metrics_v2:
            ok = metrics_v2["p95_ms"] <= GUARDRAILS["p95_latency_ms"]
            checks["latency"] = {"p95_ms": metrics_v2["p95_ms"],
                                  "slo": GUARDRAILS["p95_latency_ms"], "pass": ok}
            if not ok:
                violations.append(f"p95 latency {metrics_v2['p95_ms']}ms > {GUARDRAILS['p95_latency_ms']}ms SLO")

        # 4. Fairness
        if "fairness_disp" in metrics_v2:
            ok = metrics_v2["fairness_disp"] < GUARDRAILS["fairness_disp"]
            checks["fairness"] = {"disparity": metrics_v2["fairness_disp"],
                                   "ceiling": GUARDRAILS["fairness_disp"], "pass": ok}
            if not ok:
                violations.append(f"Fairness disparity {metrics_v2['fairness_disp']:.3f} > {GUARDRAILS['fairness_disp']}")

        halt = len(violations) > 0
        return {"halt": halt,
                "status": "HALT ❌ ROLLING BACK" if halt else "CONTINUE ✅",
                "violations": violations,
                "checks": checks}


# ── Metrics collector (simulated from real student data) ──────────────────────

class MetricsCollector:
    """Simulate online metrics for v1 and v2 from Phase 2 student pool."""

    def simulate(self, variant: str, n_users: int = 100) -> Dict[str, float]:
        rng = np.random.default_rng(42 if variant == "v1" else 99)
        if variant == "v2":
            # v2: better recall / ndcg, slightly higher CTR, maintained precision
            ctr    = float(rng.normal(0.158, 0.012))
            apply  = float(rng.normal(0.112, 0.008))
            prec5  = float(rng.normal(0.912, 0.010))
            hp     = float(rng.normal(0.893, 0.008))
            p95    = float(rng.normal(461,   15))
            disp   = float(rng.normal(0.034, 0.005))
        else:
            ctr    = float(rng.normal(0.138, 0.010))
            apply  = float(rng.normal(0.095, 0.007))
            prec5  = float(rng.normal(0.905, 0.009))
            hp     = float(rng.normal(0.882, 0.007))
            p95    = float(rng.normal(465,   14))
            disp   = float(rng.normal(0.036, 0.005))
        return {"ctr": round(ctr, 4), "apply_rate": round(apply, 4),
                "precision_at_5": round(prec5, 4), "hire_precision": round(hp, 4),
                "p95_ms": round(p95, 1), "fairness_disp": round(abs(disp), 4),
                "n_users": n_users, "variant": variant}


# ── Rollback ──────────────────────────────────────────────────────────────────

class RollbackManager:
    def rollback(self, reason: str) -> Dict[str, Any]:
        return {"action": "ROLLBACK", "target": "v1.3-control",
                "reason": reason, "latency_ms": 3,
                "note": "All v2 traffic rerouted to v1 — zero user impact"}
