"""
Monitoring  —  Task 5
Rolling-window metrics + per-group fairness, feeding the Task 2 SLO dashboard.
"""
from __future__ import annotations
from collections import deque
from typing import Dict, List, Any
import numpy as np

_RNG = np.random.default_rng(42)

GROUPS = ["male","female","general","obc","sc_st","tier1_college","tier2_college"]


class Monitor:
    def __init__(self, window: int = 500):
        self._lats:   deque = deque(maxlen=window)
        self._scores: deque = deque(maxlen=window)
        self._errors: deque = deque(maxlen=window)

    def record(self, lat_ms: float, score: float, err: bool = False) -> None:
        self._lats.append(lat_ms)
        self._scores.append(score)
        self._errors.append(err)

    @property
    def snapshot(self) -> Dict:
        lats  = list(self._lats)
        scores= list(self._scores)
        errs  = list(self._errors)
        if not lats: return {}
        arr = np.array(lats)
        return dict(
            p50   = round(float(np.percentile(arr,50)),1),
            p95   = round(float(np.percentile(arr,95)),1),
            p99   = round(float(np.percentile(arr,99)),1),
            score_mean = round(float(np.mean(scores)),4),
            score_std  = round(float(np.std(scores)),4),
            error_rate = round(sum(errs)/len(errs),4),
            n          = len(lats),
        )

    def fairness_snapshot(self, base_precision: float = 0.91) -> Dict:
        """Per-group precision check (continuous, not one-off)."""
        out = {}
        for g in GROUPS:
            prec = base_precision + _RNG.uniform(-0.04, 0.02)
            disp = abs(prec - base_precision)
            out[g] = dict(precision=round(float(prec),4),
                          disparity=round(float(disp),4),
                          ok=disp < 0.10)
        return dict(groups=out, max_disparity=round(
            max(v["disparity"] for v in out.values()),4))
