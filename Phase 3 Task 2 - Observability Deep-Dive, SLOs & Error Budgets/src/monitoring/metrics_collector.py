"""
Metrics Collector — sliding-window stats over live inference requests.
"""

from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import numpy as np


class MetricsWindow:
    """Rolling window of recent inference observations."""

    def __init__(self, window_minutes: int = 5, max_samples: int = 10_000):
        self.window_minutes = window_minutes
        self.max_samples    = max_samples
        self._latencies: deque = deque(maxlen=max_samples)
        self._scores:    deque = deque(maxlen=max_samples)
        self._errors:    deque = deque(maxlen=max_samples)   # True = error
        self._timestamps: deque = deque(maxlen=max_samples)

    def record(self, latency_ms: float, score: float,
               is_error: bool = False) -> None:
        now = datetime.utcnow()
        self._latencies.append(latency_ms)
        self._scores.append(score)
        self._errors.append(is_error)
        self._timestamps.append(now)

    def _cutoff(self) -> datetime:
        return datetime.utcnow() - timedelta(minutes=self.window_minutes)

    def _recent(self, seq: deque) -> List:
        cutoff = self._cutoff()
        return [v for v, t in zip(seq, self._timestamps) if t >= cutoff]

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def latency_percentiles(self) -> Dict[str, float]:
        data = self._recent(self._latencies)
        if not data:
            return {"p50": 0, "p95": 0, "p99": 0}
        arr = np.array(data)
        return {
            "p50": round(float(np.percentile(arr, 50)), 1),
            "p95": round(float(np.percentile(arr, 95)), 1),
            "p99": round(float(np.percentile(arr, 99)), 1),
        }

    @property
    def score_stats(self) -> Dict[str, float]:
        data = self._recent(self._scores)
        if not data:
            return {"mean": 0, "std": 0, "min": 0, "max": 0, "range": 0}
        arr = np.array(data)
        return {
            "mean":  round(float(arr.mean()), 4),
            "std":   round(float(arr.std()),  4),
            "min":   round(float(arr.min()),  4),
            "max":   round(float(arr.max()),  4),
            "range": round(float(arr.max() - arr.min()), 4),
        }

    @property
    def request_stats(self) -> Dict[str, Any]:
        errs  = self._recent(self._errors)
        total = len(errs)
        n_err = sum(errs)
        return {
            "total":        total,
            "errors":       n_err,
            "error_rate":   round(n_err / total, 6) if total else 0,
            "availability": round(1 - n_err / total, 6) if total else 1.0,
        }

    def snapshot(self) -> Dict[str, Any]:
        return {
            "window_minutes":   self.window_minutes,
            "timestamp":        datetime.utcnow().isoformat(),
            "latency":          self.latency_percentiles,
            "scores":           self.score_stats,
            "requests":         self.request_stats,
            "sample_count":     len(self._recent(self._latencies)),
        }
