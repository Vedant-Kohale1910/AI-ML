"""SLO Checker  —  Task 5  (inherits contract from Task 2)"""
from __future__ import annotations
from typing import Dict, List, Any
import numpy as np

# ── SLO targets (Task 2 contract) ───────────────────────────────────────────
SLO = dict(
    p95_latency_ms   = 500,
    availability     = 0.999,
    max_error_rate   = 0.001,
    min_precision    = 0.85,
    min_recall       = 0.80,
    max_fpr          = 0.15,
    min_score_std    = 0.05,   # degenerate-output guard
)


class SLOChecker:
    def check_latency(self, latencies_ms: List[float]) -> Dict:
        arr = np.array(latencies_ms)
        p95 = float(np.percentile(arr, 95))
        p99 = float(np.percentile(arr, 99))
        ok  = p95 <= SLO["p95_latency_ms"]
        return dict(p50=round(float(np.percentile(arr,50)),1),
                    p95=round(p95,1), p99=round(p99,1),
                    target=SLO["p95_latency_ms"], pass_=ok,
                    reason="✓ Latency SLO met" if ok
                           else f"✗ p95={p95:.0f}ms > {SLO['p95_latency_ms']}ms SLO")

    def check_availability(self, total: int, errors: int) -> Dict:
        err_rate = errors / total if total else 0
        avail    = 1 - err_rate
        ok       = avail >= SLO["availability"]
        return dict(availability=round(avail,6), error_rate=round(err_rate,6),
                    target=SLO["availability"], pass_=ok,
                    reason="✓ Availability SLO met" if ok
                           else f"✗ Availability {avail*100:.3f}% < {SLO['availability']*100}%")

    def check_quality(self, precision: float, recall: float, fpr: float) -> Dict:
        p_ok = precision >= SLO["min_precision"]
        r_ok = recall    >= SLO["min_recall"]
        f_ok = fpr       <= SLO["max_fpr"]
        ok   = p_ok and r_ok and f_ok
        viols = []
        if not p_ok: viols.append(f"precision {precision:.3f}<{SLO['min_precision']}")
        if not r_ok: viols.append(f"recall {recall:.3f}<{SLO['min_recall']}")
        if not f_ok: viols.append(f"FPR {fpr:.3f}>{SLO['max_fpr']}")
        return dict(precision=precision, recall=recall, fpr=fpr,
                    pass_=ok, violations=viols,
                    reason="✓ Quality SLO met" if ok else "✗ " + "; ".join(viols))

    def check_score_distribution(self, scores: List[float]) -> Dict:
        arr = np.array(scores)
        std = float(arr.std())
        ok  = std >= SLO["min_score_std"]
        return dict(std=round(std,4), mean=round(float(arr.mean()),4),
                    range=round(float(arr.max()-arr.min()),4),
                    pass_=ok,
                    reason="✓ Score distribution healthy" if ok
                           else f"✗ DEGENERATE OUTPUT — std={std:.4f}")

    def full_check(self, latencies_ms, total, errors, precision,
                   recall, fpr, scores) -> Dict:
        lat   = self.check_latency(latencies_ms)
        avail = self.check_availability(total, errors)
        qual  = self.check_quality(precision, recall, fpr)
        dist  = self.check_score_distribution(scores)
        all_ok = all(c["pass_"] for c in [lat, avail, qual, dist])
        return dict(overall=all_ok,
                    status="PASS ✅" if all_ok else "FAIL ❌",
                    latency=lat, availability=avail,
                    quality=qual, distribution=dist)
