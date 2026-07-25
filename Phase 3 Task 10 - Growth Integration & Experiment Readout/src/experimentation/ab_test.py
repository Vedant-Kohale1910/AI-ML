"""
A/B Experiment Platform — Task 10
Stage B: Pre-registered A/B experiment
Stage C: Honest readout (effect size, significance, guardrails)
Stage D: Ship / Do-Not-Ship decision
"""
from __future__ import annotations
import hashlib, math
from typing import Dict, List, Any
import numpy as np
from scipy import stats

RNG = np.random.default_rng(42)

# ── Pre-registration (written BEFORE seeing results) ─────────────────────────
PREREGISTRATION = {
    "experiment_name":    "rec-v2-vs-v1",
    "hypothesis":         "v2 increases CTR by ≥5% over v1 without degrading hire precision",
    "primary_metric":     "CTR",
    "secondary_metrics":  ["apply_rate","hire_precision","ndcg_at_5"],
    "guardrail_metrics":  ["hire_precision","p95_ms","fairness_disparity"],
    "min_ctr_lift":       0.05,     # 5% relative lift required to ship
    "alpha":              0.05,     # significance level
    "power":              0.80,
    "min_sample":         100,      # per arm before evaluation
    "duration_days":      14,
    "traffic_split":      {"v1": 0.90, "v2": 0.10},
    "registered_at":      "2024-01-15T09:00:00Z",
    "guardrail_floors":   {"hire_precision": 0.85, "p95_ms": 500, "fairness_disparity": 0.10},
}


class VariantRouter:
    """Consistent hash-based assignment — same user → same variant always."""
    def assign(self, user_id: int) -> str:
        bucket = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16) % 100
        return "v2" if bucket < 10 else "v1"


class MetricsSimulator:
    """Simulate online metrics from Phase 2 student data with realistic distributions."""
    def simulate(self, variant: str, n: int = 200) -> Dict[str, Any]:
        rng = np.random.default_rng(42 if variant=="v1" else 77)
        if variant == "v2":
            clicks   = rng.binomial(1, 0.19, n)
            applies  = rng.binomial(1, 0.135, n)
            hp       = float(rng.normal(0.892, 0.008))
            ndcg     = float(rng.normal(0.848, 0.010))
            p95      = float(rng.normal(461,   15))
            fairness = float(abs(rng.normal(0.034, 0.005)))
        else:
            clicks   = rng.binomial(1, 0.138, n)
            applies  = rng.binomial(1, 0.095, n)
            hp       = float(rng.normal(0.882, 0.007))
            ndcg     = float(rng.normal(0.832, 0.009))
            p95      = float(rng.normal(465,   14))
            fairness = float(abs(rng.normal(0.036, 0.005)))
        return {
            "variant": variant, "n": n,
            "clicks": clicks, "applies": applies,
            "ctr": round(float(clicks.mean()), 4),
            "apply_rate": round(float(applies.mean()), 4),
            "hire_precision": round(hp, 4),
            "ndcg_at_5": round(ndcg, 4),
            "p95_ms": round(p95, 1),
            "fairness_disparity": round(fairness, 4),
        }


class ExperimentReadout:
    """Stage C: Honest readout — no cherry-picking."""

    def significance_test(self, v1: Dict, v2: Dict) -> Dict[str, Any]:
        """Two-proportion z-test on CTR (pre-registered primary metric)."""
        n1, n2 = v1["n"], v2["n"]
        p1, p2 = v1["ctr"], v2["ctr"]
        p_pool = (p1*n1 + p2*n2) / (n1+n2)
        se     = math.sqrt(p_pool*(1-p_pool)*(1/n1 + 1/n2))
        z      = (p2 - p1) / se if se > 0 else 0
        p_val  = float(2 * (1 - stats.norm.cdf(abs(z))))   # two-tailed
        ci_lo  = (p2-p1) - 1.96*se
        ci_hi  = (p2-p1) + 1.96*se
        return {
            "z_stat":      round(z, 3),
            "p_value":     round(p_val, 4),
            "significant": p_val < PREREGISTRATION["alpha"],
            "ci_95":       (round(ci_lo,4), round(ci_hi,4)),
            "effect_size": round((p2-p1)/p1*100, 2),  # relative % lift
        }

    def guardrail_check(self, v2: Dict) -> Dict[str, Any]:
        floors = PREREGISTRATION["guardrail_floors"]
        checks = {
            "hire_precision": {"value": v2["hire_precision"], "floor": floors["hire_precision"],
                               "pass": v2["hire_precision"] >= floors["hire_precision"]},
            "latency_p95":    {"value": v2["p95_ms"],         "floor": floors["p95_ms"],
                               "pass": v2["p95_ms"] <= floors["p95_ms"]},
            "fairness":       {"value": v2["fairness_disparity"], "floor": floors["fairness_disparity"],
                               "pass": v2["fairness_disparity"] < floors["fairness_disparity"]},
        }
        return {"checks": checks, "all_pass": all(c["pass"] for c in checks.values())}

    def practical_significance(self, effect_pct: float, significant: bool) -> Dict[str, Any]:
        """Is a statistically real lift also worth shipping?"""
        min_lift = PREREGISTRATION["min_ctr_lift"] * 100   # convert to %
        practical = significant and effect_pct >= min_lift
        return {"effect_pct": effect_pct, "min_required_pct": min_lift,
                "stat_sig": significant, "practical_sig": practical,
                "verdict": "PRACTICALLY SIGNIFICANT" if practical else
                           ("STAT SIG BUT TOO SMALL" if significant else "NOT SIGNIFICANT")}


class ShipDecision:
    """Stage D: Evidence-based ship / do-not-ship."""

    def decide(self, sig: Dict, guardrails: Dict, practical: Dict,
               v1: Dict, v2: Dict) -> Dict[str, Any]:
        ship = (practical["practical_sig"] and guardrails["all_pass"])
        reasons = []
        if practical["stat_sig"]:
            reasons.append(f"CTR lift +{practical['effect_pct']:.1f}%% is statistically significant "
                           f"(p={sig['p_value']:.4f} < 0.05)")
        else:
            reasons.append(f"CTR lift not significant (p={sig['p_value']:.4f} ≥ 0.05)")
        if practical["practical_sig"]:
            reasons.append(f"Lift {practical['effect_pct']:.1f}%% ≥ {practical['min_required_pct']:.0f}%% threshold")
        else:
            reasons.append(f"Lift {practical['effect_pct']:.1f}%% < {practical['min_required_pct']:.0f}%% threshold")
        if guardrails["all_pass"]:
            reasons.append("All guardrail metrics within bounds")
        else:
            failing = [k for k,v in guardrails["checks"].items() if not v["pass"]]
            reasons.append(f"GUARDRAIL BREACH: {', '.join(failing)}")

        return {"decision": "SHIP ✅" if ship else "DO NOT SHIP ❌", "ship": ship,
                "reasons": reasons, "model": "v2.0-treatment" if ship else "keep v1.3-control"}
