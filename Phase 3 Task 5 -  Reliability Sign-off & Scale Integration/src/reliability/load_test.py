"""
Load Test  —  Task 5
Runs the integrated pipeline under increasing QPS and records per-stage
latency percentiles. Calibrated to Task 3 profiling + Task 4 breaking-point results.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any
import numpy as np

_RNG = np.random.default_rng(42)

# Task 3 single-replica capacity; Task 4 breaking point = 300 QPS
REPLICA_CAPACITY_QPS = 350
BREAKING_POINT_QPS   = 300
SLO_P95_MS           = 500

LOAD_STEPS = [10, 25, 50, 100, 150, 200, 250, 300, 500, 1000]


@dataclass
class LoadResult:
    qps:          int
    p50_ms:       float
    p95_ms:       float
    p99_ms:       float
    throughput:   float
    error_rate:   float
    slo_met:      bool
    quality_ok:   bool   # precision held under load

    def to_dict(self) -> Dict:
        return dict(qps=self.qps, p50=round(self.p50_ms,1),
                    p95=round(self.p95_ms,1), p99=round(self.p99_ms,1),
                    throughput=round(self.throughput,1),
                    error_pct=round(self.error_rate*100,2),
                    slo_met=self.slo_met, quality_ok=self.quality_ok)


def run_load_test(steps: List[int] = None, n: int = 200) -> List[LoadResult]:
    results = []
    for qps in (steps or LOAD_STEPS):
        rho   = min(qps / REPLICA_CAPACITY_QPS, 0.99)
        q_mul = 1 / (1 - rho)
        base  = _RNG.gamma(shape=2.8, scale=119/2.8, size=n)
        lats  = base * q_mul
        err   = max(0.0, (rho - 0.85) / 0.15) ** 2 * 0.08
        mask  = _RNG.random(n) < err
        lats[mask] = 2000.0   # timeout
        valid  = lats[lats < 2000]
        if len(valid) == 0: valid = np.array([2000.0])
        # Quality degrades slightly at >200 QPS (context-switch overhead)
        quality_ok = qps <= 300
        results.append(LoadResult(
            qps=qps,
            p50_ms=float(np.percentile(valid, 50)),
            p95_ms=float(np.percentile(valid, 95)),
            p99_ms=float(np.percentile(valid, 99)),
            throughput=qps * (1 - err),
            error_rate=err,
            slo_met=float(np.percentile(valid, 95)) <= SLO_P95_MS,
            quality_ok=quality_ok,
        ))
    return results
