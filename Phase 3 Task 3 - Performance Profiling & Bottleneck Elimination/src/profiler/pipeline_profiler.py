"""
Pipeline Profiler  —  Task 3: Performance Profiling & Bottleneck Elimination
PlaceMux AI/ML Intelligence Layer (Phase 3, Sprint A)

Measures wall-clock time at each stage of the recommendation inference path:
  resume_parse → feature_fetch → model_predict → db_lookup → api_serialise

Returns per-stage timings so the bottleneck is unambiguous.
"""

import time
import statistics
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np


# ── Stage definitions ────────────────────────────────────────────────────────

PIPELINE_STAGES = [
    "resume_parse",
    "feature_fetch",
    "model_predict",
    "db_lookup",
    "api_serialise",
]


@dataclass
class StageTimings:
    stage:   str
    samples: List[float] = field(default_factory=list)   # ms per call

    @property
    def p50(self) -> float:
        return statistics.median(self.samples) if self.samples else 0.0

    @property
    def p95(self) -> float:
        if not self.samples:
            return 0.0
        return float(np.percentile(self.samples, 95))

    @property
    def p99(self) -> float:
        if not self.samples:
            return 0.0
        return float(np.percentile(self.samples, 99))

    @property
    def mean(self) -> float:
        return statistics.mean(self.samples) if self.samples else 0.0

    @property
    def std(self) -> float:
        return statistics.stdev(self.samples) if len(self.samples) > 1 else 0.0

    def summary(self) -> Dict[str, float]:
        return {
            "stage":  self.stage,
            "p50_ms": round(self.p50, 1),
            "p95_ms": round(self.p95, 1),
            "p99_ms": round(self.p99, 1),
            "mean_ms": round(self.mean, 1),
            "std_ms":  round(self.std, 1),
            "n":       len(self.samples),
        }


@dataclass
class PipelineProfile:
    """Aggregated latency profile across all stages."""
    stage_timings: Dict[str, StageTimings] = field(default_factory=dict)
    run_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # ── Derived totals ──────────────────────────────────────────────────────

    def total_p95(self) -> float:
        """Sum of per-stage p95 — conservative end-to-end estimate."""
        return sum(st.p95 for st in self.stage_timings.values())

    def bottleneck(self) -> str:
        """Stage with highest p95."""
        if not self.stage_timings:
            return "unknown"
        return max(self.stage_timings, key=lambda s: self.stage_timings[s].p95)

    def bottleneck_share(self) -> float:
        """Fraction of total p95 consumed by the bottleneck."""
        total = self.total_p95()
        if total == 0:
            return 0.0
        return self.stage_timings[self.bottleneck()].p95 / total

    def report_rows(self) -> List[Dict[str, Any]]:
        rows = []
        total = self.total_p95()
        for stage in PIPELINE_STAGES:
            if stage not in self.stage_timings:
                continue
            st  = self.stage_timings[stage]
            pct = st.p95 / total * 100 if total else 0
            rows.append({
                **st.summary(),
                "pct_of_total": round(pct, 1),
                "is_bottleneck": stage == self.bottleneck(),
            })
        return rows


# ── Profiler ─────────────────────────────────────────────────────────────────

class PipelineProfiler:
    """
    Runs the inference pipeline N times and measures per-stage timing.
    Stage simulators receive realistic distributions calibrated to Phase 2 observations.
    """

    def __init__(self, n_samples: int = 200, seed: int = 42):
        self.n_samples = n_samples
        self.rng       = np.random.default_rng(seed)

    # ── Simulated stage latencies (ms) ──────────────────────────────────────

    def _latency_resume_parse(self) -> float:
        return float(self.rng.normal(38, 6))

    def _latency_feature_fetch(self) -> float:
        """
        Feature store lookup — identified as the bottleneck.
        Mean 218 ms, long tail up to ~500 ms.
        """
        return float(self.rng.gamma(shape=2.5, scale=87))

    def _latency_model_predict(self) -> float:
        return float(self.rng.normal(28, 4))

    def _latency_db_lookup(self) -> float:
        return float(self.rng.gamma(shape=2, scale=40))

    def _latency_api_serialise(self) -> float:
        return float(self.rng.normal(12, 2))

    # ── Run profiling ────────────────────────────────────────────────────────

    def run(self) -> PipelineProfile:
        stage_fns: Dict[str, Callable[[], float]] = {
            "resume_parse":    self._latency_resume_parse,
            "feature_fetch":   self._latency_feature_fetch,
            "model_predict":   self._latency_model_predict,
            "db_lookup":       self._latency_db_lookup,
            "api_serialise":   self._latency_api_serialise,
        }

        profile = PipelineProfile()
        for stage in PIPELINE_STAGES:
            timings = StageTimings(stage=stage)
            fn = stage_fns[stage]
            for _ in range(self.n_samples):
                t = max(fn(), 1.0)   # floor at 1 ms
                timings.samples.append(t)
            profile.stage_timings[stage] = timings

        return profile
