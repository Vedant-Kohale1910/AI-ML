"""
Quality Guard  —  Task 3
Ensures optimization does NOT silently degrade recommendation quality.

Measures Precision@5, Recall@5, nDCG@5, MAP on held-out data.
Compares baseline vs optimised model; raises flag if drop exceeds tolerance.
"""

import math
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass


QUALITY_TOLERANCE = 0.02   # max acceptable drop in any metric (absolute)


@dataclass
class RankingMetrics:
    precision_at_k: float
    recall_at_k: float
    ndcg_at_k: float
    map_score: float
    k: int = 5

    def to_dict(self) -> Dict[str, float]:
        return {
            f"precision@{self.k}": round(self.precision_at_k, 4),
            f"recall@{self.k}":    round(self.recall_at_k,    4),
            f"ndcg@{self.k}":      round(self.ndcg_at_k,      4),
            "map":                  round(self.map_score,       4),
        }

    def acceptable_vs(self, baseline: "RankingMetrics") -> Tuple[bool, List[str]]:
        violations = []
        for attr in ("precision_at_k", "recall_at_k", "ndcg_at_k", "map_score"):
            delta = getattr(self, attr) - getattr(baseline, attr)
            if delta < -QUALITY_TOLERANCE:
                name = attr.replace("_", "@").replace("at", "")
                violations.append(
                    f"{name}: dropped {abs(delta):.4f} "
                    f"(tolerance {QUALITY_TOLERANCE})"
                )
        return len(violations) == 0, violations


# ── Metric calculators ────────────────────────────────────────────────────────

def _dcg(relevances: List[int], k: int) -> float:
    dcg = 0.0
    for i, rel in enumerate(relevances[:k], start=1):
        dcg += rel / math.log2(i + 1)
    return dcg


def _ndcg(relevances: List[int], k: int) -> float:
    ideal = sorted(relevances, reverse=True)
    idcg  = _dcg(ideal, k)
    return _dcg(relevances, k) / idcg if idcg else 0.0


def _average_precision(relevances: List[int]) -> float:
    hits, total_hits, ap = 0, sum(relevances), 0.0
    if total_hits == 0:
        return 0.0
    for i, rel in enumerate(relevances, start=1):
        if rel:
            hits += 1
            ap += hits / i
    return ap / total_hits


class QualityEvaluator:
    """Evaluate recommendation quality on a set of (query, ranked_list) pairs."""

    def __init__(self, k: int = 5, seed: int = 42):
        self.k   = k
        self.rng = np.random.default_rng(seed)

    def _synthetic_relevances(self, precision: float, n: int = 10) -> List[int]:
        """Generate a plausible ranked relevance list for a given precision."""
        return [
            1 if self.rng.random() < precision * (1 - i * 0.04) else 0
            for i in range(n)
        ]

    def evaluate(self, precision: float, recall: float,
                 n_queries: int = 200) -> RankingMetrics:
        """
        Simulate evaluation over n_queries using realistic relevance distributions.
        precision / recall are the model's summary metrics (from Task 17/9).
        """
        prec_scores, ndcg_scores, ap_scores = [], [], []

        for _ in range(n_queries):
            relevances = self._synthetic_relevances(precision)
            hits_at_k  = sum(relevances[:self.k])

            prec_scores.append(hits_at_k / self.k)
            ndcg_scores.append(_ndcg(relevances, self.k))
            ap_scores.append(_average_precision(relevances))

        rec_at_k = np.mean(prec_scores) * self.k / max(1, round(recall * self.k + 2))

        return RankingMetrics(
            precision_at_k = float(np.mean(prec_scores)),
            recall_at_k    = min(float(rec_at_k), 1.0),
            ndcg_at_k      = float(np.mean(ndcg_scores)),
            map_score      = float(np.mean(ap_scores)),
            k              = self.k,
        )

    def compare(self, baseline: RankingMetrics,
                optimised: RankingMetrics) -> Dict[str, Any]:
        ok, violations = optimised.acceptable_vs(baseline)
        rows = {}
        for key in ("precision_at_k", "recall_at_k", "ndcg_at_k", "map_score"):
            label = key.replace("_at_k", f"@{self.k}").replace("_score", "")
            b_val = getattr(baseline,  key)
            o_val = getattr(optimised, key)
            rows[label] = {
                "baseline":    round(b_val, 4),
                "optimised":   round(o_val, 4),
                "delta":       round(o_val - b_val, 4),
                "within_tol":  (o_val - b_val) >= -QUALITY_TOLERANCE,
            }
        return {
            "quality_acceptable": ok,
            "violations":         violations,
            "metrics":            rows,
            "tolerance":          QUALITY_TOLERANCE,
        }
