"""
SLO Checker — evaluates a window of observations against defined SLOs.
Returns per-SLO pass/fail and human-readable reasons.
"""

from typing import Dict, List, Any
import numpy as np

from src.slo.definitions import InferenceSLO, INFERENCE_SLO


class SLOChecker:
    def __init__(self, slo: InferenceSLO = INFERENCE_SLO):
        self.slo = slo

    # ── Latency ───────────────────────────────────────────────────────────────

    def check_latency(self, latencies_ms: List[float]) -> Dict[str, Any]:
        arr = np.array(latencies_ms)
        p50 = float(np.percentile(arr, 50))
        p95 = float(np.percentile(arr, 95))
        p99 = float(np.percentile(arr, 99))

        p95_ok = p95 <= self.slo.p95_latency_ms
        p99_ok = p99 <= self.slo.p99_latency_ms
        p50_ok = p50 <= self.slo.p50_latency_ms

        return {
            "name": "inference_latency",
            "p50_ms":      round(p50, 1),
            "p95_ms":      round(p95, 1),
            "p99_ms":      round(p99, 1),
            "p50_target":  self.slo.p50_latency_ms,
            "p95_target":  self.slo.p95_latency_ms,
            "p99_target":  self.slo.p99_latency_ms,
            "p50_ok":      p50_ok,
            "p95_ok":      p95_ok,
            "p99_ok":      p99_ok,
            "pass":        p95_ok and p99_ok,
            "reason": (
                "All latency percentiles within SLO"
                if p95_ok and p99_ok
                else f"p95={p95:.0f}ms exceeds {self.slo.p95_latency_ms}ms target"
                     if not p95_ok
                     else f"p99={p99:.0f}ms exceeds {self.slo.p99_latency_ms}ms target"
            ),
        }

    # ── Availability ──────────────────────────────────────────────────────────

    def check_availability(self, total_requests: int,
                           error_requests: int) -> Dict[str, Any]:
        error_rate   = error_requests / total_requests if total_requests else 0
        availability = 1 - error_rate
        ok           = availability >= self.slo.availability_target

        return {
            "name":              "availability",
            "total_requests":    total_requests,
            "error_requests":    error_requests,
            "error_rate":        round(error_rate, 6),
            "availability":      round(availability, 6),
            "target":            self.slo.availability_target,
            "pass":              ok,
            "reason": (
                f"Availability {availability*100:.3f}% meets {self.slo.availability_target*100}% SLO"
                if ok
                else f"Availability {availability*100:.3f}% below {self.slo.availability_target*100}% SLO"
            ),
        }

    # ── Prediction quality ────────────────────────────────────────────────────

    def check_quality(self, precision: float, recall: float,
                      fpr: float) -> Dict[str, Any]:
        f1 = (2 * precision * recall / (precision + recall)
              if (precision + recall) else 0)

        prec_ok  = precision >= self.slo.min_precision
        rec_ok   = recall    >= self.slo.min_recall
        fpr_ok   = fpr       <= self.slo.max_fpr
        f1_ok    = f1        >= self.slo.min_f1
        all_ok   = prec_ok and rec_ok and fpr_ok and f1_ok

        violations = []
        if not prec_ok:
            violations.append(f"precision {precision:.3f} < floor {self.slo.min_precision}")
        if not rec_ok:
            violations.append(f"recall {recall:.3f} < floor {self.slo.min_recall}")
        if not fpr_ok:
            violations.append(f"FPR {fpr:.3f} > cap {self.slo.max_fpr}")
        if not f1_ok:
            violations.append(f"F1 {f1:.3f} < floor {self.slo.min_f1}")

        return {
            "name":           "prediction_quality",
            "precision":      round(precision, 4),
            "recall":         round(recall,    4),
            "fpr":            round(fpr,       4),
            "f1":             round(f1,        4),
            "precision_ok":   prec_ok,
            "recall_ok":      rec_ok,
            "fpr_ok":         fpr_ok,
            "f1_ok":          f1_ok,
            "pass":           all_ok,
            "reason": "All quality metrics above SLO floors" if all_ok
                      else "; ".join(violations),
        }

    # ── Score distribution (degenerate-output guard) ─────────────────────────

    def check_score_distribution(self, scores: List[float]) -> Dict[str, Any]:
        arr    = np.array(scores)
        std    = float(np.std(arr))
        rng    = float(arr.max() - arr.min())
        std_ok = std >= self.slo.min_score_std
        rng_ok = rng >= self.slo.min_score_range
        ok     = std_ok and rng_ok

        return {
            "name":        "score_distribution",
            "std":         round(std, 4),
            "range":       round(rng, 4),
            "mean":        round(float(arr.mean()), 4),
            "min":         round(float(arr.min()), 4),
            "max":         round(float(arr.max()), 4),
            "std_target":  self.slo.min_score_std,
            "range_target": self.slo.min_score_range,
            "std_ok":      std_ok,
            "range_ok":    rng_ok,
            "pass":        ok,
            "reason": "Score distribution healthy" if ok
                      else f"DEGENERATE OUTPUT DETECTED — std={std:.4f} range={rng:.4f}",
        }

    # ── Full report ───────────────────────────────────────────────────────────

    def full_check(self, latencies_ms: List[float], total_requests: int,
                   error_requests: int, precision: float, recall: float,
                   fpr: float, scores: List[float]) -> Dict[str, Any]:
        lat   = self.check_latency(latencies_ms)
        avail = self.check_availability(total_requests, error_requests)
        qual  = self.check_quality(precision, recall, fpr)
        dist  = self.check_score_distribution(scores)

        all_pass = all(r["pass"] for r in [lat, avail, qual, dist])

        return {
            "overall_pass":   all_pass,
            "overall_status": "HEALTHY" if all_pass else "BREACH",
            "checks": {
                "latency":            lat,
                "availability":       avail,
                "prediction_quality": qual,
                "score_distribution": dist,
            },
        }
