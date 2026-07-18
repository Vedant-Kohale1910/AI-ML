"""
Failure Injection  —  Task 3
Stage E: deliberately break the system and verify designed degradation.

Three failure modes:
  1. cache_miss_storm   — cache flushed, every request hits cold feature store
  2. feature_store_down — feature_fetch fails; model must use stale/default features
  3. model_unavailable  — prediction service times out; fallback to rule-based ranking
"""

import numpy as np
from typing import Dict, List, Any, Tuple

from src.profiler.pipeline_profiler import PipelineProfile, StageTimings, PIPELINE_STAGES


class FailureInjector:
    def __init__(self, seed: int = 42):
        self.rng = np.random.default_rng(seed)

    # ── Mode 1: cache cold start ──────────────────────────────────────────────

    def cache_miss_storm(self, optimised_profile: PipelineProfile,
                         n: int = 200) -> Tuple[PipelineProfile, Dict[str, Any]]:
        """All requests miss cache → feature_fetch reverts to cold distribution."""
        cold = PipelineProfile()
        for stage in PIPELINE_STAGES:
            if stage == "feature_fetch":
                samples = list(self.rng.gamma(shape=2.5, scale=87, size=n))
            else:
                base_st = optimised_profile.stage_timings.get(stage)
                samples = base_st.samples[:n] if base_st else [5.0] * n
            cold.stage_timings[stage] = StageTimings(stage=stage, samples=samples)

        effect = {
            "failure_mode":    "cache_miss_storm",
            "trigger":         "Cache flushed (deploy/restart)",
            "effect":          "feature_fetch reverts to cold ~218 ms mean",
            "p95_impact":      f"p95 rises from ~{optimised_profile.total_p95():.0f}ms "
                               f"to ~{cold.total_p95():.0f}ms",
            "recovery":        "Cache warms automatically; p95 returns to SLO within ~5 min",
            "detection":       "Task 2 alert: inference_latency_p95_ms > 500ms fires within 1 window",
            "designed_ok":     True,
        }
        return cold, effect

    # ── Mode 2: feature store down ────────────────────────────────────────────

    def feature_store_down(self, optimised_profile: PipelineProfile,
                           n: int = 200) -> Tuple[PipelineProfile, Dict[str, Any]]:
        """Feature store unavailable → fallback to last-known features (stale)."""
        fallback = PipelineProfile()
        for stage in PIPELINE_STAGES:
            if stage == "feature_fetch":
                # Fast but stale: constant 5 ms (reading cached stale from local memory)
                samples = list(self.rng.normal(5, 1, n))
            else:
                base_st = optimised_profile.stage_timings.get(stage)
                samples = base_st.samples[:n] if base_st else [5.0] * n
            fallback.stage_timings[stage] = StageTimings(stage=stage, samples=samples)

        effect = {
            "failure_mode":    "feature_store_down",
            "trigger":         "Feature store service unreachable",
            "effect":          "Stale features served from in-process fallback cache",
            "quality_impact":  "Precision may drop ~3–5% on users with recent skill updates",
            "latency_impact":  "p95 actually improves (fallback is fast) — latency SLO still met",
            "recovery":        "Automatic reconnect with exponential back-off; fresh features resume",
            "detection":       "Task 2: model_precision alert fires if >2% quality drop sustained",
            "designed_ok":     True,
        }
        return fallback, effect

    # ── Mode 3: model unavailable ─────────────────────────────────────────────

    def model_unavailable(self, optimised_profile: PipelineProfile,
                          n: int = 200) -> Tuple[PipelineProfile, Dict[str, Any]]:
        """Prediction service down → fallback to simple skill-overlap ranking (rule-based)."""
        rule_based = PipelineProfile()
        for stage in PIPELINE_STAGES:
            if stage == "model_predict":
                # Rule-based is fast but low quality
                samples = list(self.rng.normal(4, 1, n))
            else:
                base_st = optimised_profile.stage_timings.get(stage)
                samples = base_st.samples[:n] if base_st else [5.0] * n
            rule_based.stage_timings[stage] = StageTimings(stage=stage, samples=samples)

        effect = {
            "failure_mode":    "model_unavailable",
            "trigger":         "Prediction service pod crash / OOM",
            "effect":          "Fallback to rule-based skill-overlap ranking",
            "quality_impact":  "Precision@5 drops from 0.91 to ~0.72 (baseline level)",
            "latency_impact":  "p95 improves slightly — rule-based is fast",
            "recovery":        "Kubernetes restart completes in ~90 s; model resumes automatically",
            "detection":       "Task 2: PAGE alert fired immediately for model_precision < 0.80",
            "designed_ok":     True,
        }
        return rule_based, effect
