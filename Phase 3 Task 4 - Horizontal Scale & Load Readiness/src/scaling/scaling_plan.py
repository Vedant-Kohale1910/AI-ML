"""
Scaling Plan  —  Task 4: Stage D
Defines the autoscaling thresholds and produces scaling recommendations
based on observed QPS and breaking-point analysis.

Three scaling strategies evaluated:
  A: Horizontal autoscale     — add replicas when p95 > 400ms (20% headroom)
  B: Precomputed scores       — nightly batch job + Redis lookup (Task 3 option)
  C: Hybrid (chosen)          — autoscale + precompute for hot students

Chosen: Hybrid (A+B) — autoscale handles bursts, precompute handles known-hot users.
"""
from __future__ import annotations
from typing import Dict, List, Any
import math


REPLICA_CAPACITY_QPS   = 350    # QPS per replica (from Task 3/load test)
TARGET_UTILISATION     = 0.70   # scale out at 70% capacity
SLO_P95_MS             = 500    # ms — from Task 2 SLO contract
SCALE_OUT_TRIGGER_MS   = 400    # trigger before SLO breach (20% headroom)
PRECOMPUTE_HOT_STUDENT_THRESHOLD = 0.15  # top 15% access frequency → precompute


class ScalingPlan:

    def replicas_needed(self, qps: int) -> int:
        """Minimum replicas to serve QPS at target utilisation."""
        return math.ceil(qps / (REPLICA_CAPACITY_QPS * TARGET_UTILISATION))

    def autoscale_recommendation(self, current_qps: int,
                                 current_p95_ms: float) -> Dict[str, Any]:
        """
        Returns scale-out / scale-in decision based on current metrics.
        Aligns with Task 2 SLO dashboard alerts.
        """
        needed  = self.replicas_needed(current_qps)
        action  = "SCALE_OUT" if current_p95_ms > SCALE_OUT_TRIGGER_MS else (
                   "SCALE_IN"  if current_p95_ms < 200 else "HOLD")
        return {
            "current_qps":          current_qps,
            "current_p95_ms":       current_p95_ms,
            "replicas_needed":      needed,
            "action":               action,
            "trigger_p95_ms":       SCALE_OUT_TRIGGER_MS,
            "reason": (
                f"p95 {current_p95_ms:.0f}ms > {SCALE_OUT_TRIGGER_MS}ms trigger → "
                f"add replica(s) to reach {needed} total"
                if action == "SCALE_OUT"
                else f"p95 {current_p95_ms:.0f}ms < 200ms → consider removing a replica"
                if action == "SCALE_IN"
                else "Within safe operating band — hold current replica count"
            ),
        }

    def precompute_eligibility(self, student_request_counts: Dict[int, int],
                               total_requests: int) -> Dict[str, Any]:
        """
        Identifies students whose scores should be precomputed nightly.
        Top 15% by access frequency → Redis cached score → 4ms lookup.
        """
        if not student_request_counts or total_requests == 0:
            return {"hot_student_ids": [], "coverage_pct": 0}

        sorted_students = sorted(student_request_counts.items(),
                                 key=lambda x: x[1], reverse=True)
        threshold_count = int(PRECOMPUTE_HOT_STUDENT_THRESHOLD * len(sorted_students))
        hot = [sid for sid, _ in sorted_students[:threshold_count]]
        hot_req_volume  = sum(c for _, c in sorted_students[:threshold_count])

        return {
            "hot_student_ids":    hot,
            "hot_student_count":  len(hot),
            "total_students":     len(student_request_counts),
            "coverage_pct":       round(hot_req_volume / total_requests * 100, 1),
            "latency_benefit":    "465ms → 4ms for hot students (Task 3 score-precompute strategy)",
        }

    def full_plan(self, breaking_point_qps: int, peak_qps: int) -> Dict[str, Any]:
        """
        Complete scaling plan from load-test results → DevOps hand-off.
        """
        peak_replicas   = self.replicas_needed(peak_qps)
        safe_qps_single = int(REPLICA_CAPACITY_QPS * TARGET_UTILISATION)

        return {
            "breaking_point_qps":  breaking_point_qps,
            "peak_qps_target":     peak_qps,
            "replicas_at_peak":    peak_replicas,
            "strategy":            "Horizontal autoscale + precomputed hot-student scores",
            "autoscale": {
                "metric":          "inference_latency_p95_ms (Task 2 SLO dashboard)",
                "scale_out_at":    f"p95 > {SCALE_OUT_TRIGGER_MS}ms",
                "scale_in_at":     "p95 < 200ms for 5 min",
                "min_replicas":    1,
                "max_replicas":    peak_replicas + 2,
                "warm_up_s":       90,   # pod start + model load
            },
            "precompute": {
                "eligible_fraction":   f"Top {PRECOMPUTE_HOT_STUDENT_THRESHOLD*100:.0f}% students by access",
                "refresh_schedule":    "Nightly 02:00 UTC (low-traffic window)",
                "latency_hot":         "4ms (Redis lookup)",
                "latency_cold":        "465ms (full pipeline)",
                "staleness":           "max 24 h (acceptable for placement context)",
            },
            "fallback": {
                "tier_2":  "Heuristic skill-overlap (<5ms) on model timeout",
                "tier_3":  "Precomputed popular-job list (<1ms) on total failure",
            },
            "rejected_alternatives": {
                "full_precompute":   "24h staleness unacceptable for active job seekers",
                "model_quantise":    "Saves only 6ms — not the bottleneck",
            },
            "devops_hand_off": {
                "k8s_hpa_metric":   "custom/inference_p95_latency",
                "redis_cluster":    "Required for precomputed score store",
                "connection_pool":  "≥ 20 connections for parallel async DB",
                "cold_start":       "Warm-up job runs at deploy time; cache pre-loaded",
            },
        }
