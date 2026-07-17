"""
Traffic Generator — produces realistic (and deliberately broken) inference logs.
Used for the Stage E failure injection demo.
"""

import numpy as np
from typing import List, Tuple, Dict, Any


RNG = np.random.default_rng(seed=42)


def _clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


class TrafficGenerator:
    """Generates per-request (latency_ms, score, is_error) tuples."""

    # ── Normal production traffic ─────────────────────────────────────────────

    def healthy_window(self, n: int = 500) -> List[Tuple[float, float, bool]]:
        """Representative healthy production traffic."""
        latencies = RNG.gamma(shape=2.0, scale=55.0, size=n)          # mean ~110 ms
        scores    = RNG.beta(a=5, b=2, size=n)                         # right-skewed 0–1
        errors    = RNG.random(n) < 0.0005                             # 0.05 % error rate
        return list(zip(latencies.tolist(), scores.tolist(), errors.tolist()))

    # ── Synthetic breach scenarios ────────────────────────────────────────────

    def latency_spike(self, n: int = 500) -> List[Tuple[float, float, bool]]:
        """p95 latency shoots above 500 ms SLO."""
        latencies = RNG.gamma(shape=2.0, scale=300.0, size=n)          # mean ~600 ms
        scores    = RNG.beta(a=5, b=2, size=n)
        errors    = RNG.random(n) < 0.002
        return list(zip(latencies.tolist(), scores.tolist(), errors.tolist()))

    def quality_degradation(self, n: int = 500) -> List[Tuple[float, float, bool]]:
        """Precision/recall drop below quality floor."""
        # We don't embed quality in per-request data; caller supplies bad P/R/FPR.
        latencies = RNG.gamma(shape=2.0, scale=55.0, size=n)
        scores    = RNG.beta(a=3, b=3, size=n)                         # more central
        errors    = RNG.random(n) < 0.001
        return list(zip(latencies.tolist(), scores.tolist(), errors.tolist()))

    def degenerate_output(self, n: int = 500) -> List[Tuple[float, float, bool]]:
        """Model stuck returning constant score — std ≈ 0."""
        latencies = RNG.gamma(shape=2.0, scale=55.0, size=n)
        scores    = [0.72 + RNG.normal(0, 0.002) for _ in range(n)]   # std ≈ 0.002
        errors    = RNG.random(n) < 0.001
        return list(zip(latencies, scores, errors.tolist()))

    def availability_crash(self, n: int = 500) -> List[Tuple[float, float, bool]]:
        """Error rate spikes to ~3 % — availability SLO breach."""
        latencies = RNG.gamma(shape=2.0, scale=55.0, size=n)
        scores    = RNG.beta(a=5, b=2, size=n)
        errors    = RNG.random(n) < 0.03                               # 3 % error rate
        return list(zip(latencies.tolist(), scores.tolist(), errors.tolist()))

    # ── Helper ────────────────────────────────────────────────────────────────

    def unpack(self, window: List[Tuple[float, float, bool]]) -> Dict[str, Any]:
        latencies = [r[0] for r in window]
        scores    = [r[1] for r in window]
        errors    = [r[2] for r in window]
        return {
            "latencies": latencies,
            "scores":    scores,
            "total":     len(window),
            "errors":    sum(errors),
        }
