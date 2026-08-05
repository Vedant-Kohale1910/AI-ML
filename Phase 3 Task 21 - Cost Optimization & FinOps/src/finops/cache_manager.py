"""
cache_manager.py — LRU cache for recommendation scores.
Preserves IDENTICAL quality (same model, same weights) — just avoids recomputation.
"""
from collections import OrderedDict
import time


class LRUCache:
    """Simple LRU cache with TTL. Key = (student_id, job_id). Value = score."""
    def __init__(self, maxsize: int = 10000, ttl_seconds: int = 3600):
        self.cache = OrderedDict()
        self.maxsize = maxsize
        self.ttl = ttl_seconds
        self.hits = 0
        self.misses = 0
        self.enabled = True   # toggle for failure scenario

    def get(self, key):
        if not self.enabled:
            self.misses += 1
            return None
        if key in self.cache:
            val, ts = self.cache[key]
            if time.time() - ts < self.ttl:
                self.cache.move_to_end(key)
                self.hits += 1
                return val
            del self.cache[key]
        self.misses += 1
        return None

    def set(self, key, value):
        if not self.enabled:
            return
        if len(self.cache) >= self.maxsize:
            self.cache.popitem(last=False)
        self.cache[key] = (value, time.time())

    def hit_rate(self):
        total = self.hits + self.misses
        return round(self.hits / max(total, 1), 4)

    def stats(self):
        return {"hits": self.hits, "misses": self.misses,
                "hit_rate": self.hit_rate(), "size": len(self.cache),
                "enabled": self.enabled}


# ── Quality validator ─────────────────────────────────────────────────────────

import math, numpy as np

def ndcg_at_5(ranked_ids, relevant_ids):
    rels = [1 if i in relevant_ids else 0 for i in ranked_ids[:5]]
    ideal = sorted(rels, reverse=True)
    dcg  = sum(r/math.log2(i+2) for i,r in enumerate(rels))
    idcg = sum(r/math.log2(i+2) for i,r in enumerate(ideal))
    return round(dcg/max(idcg,1e-9), 4)


def precision_at_5(ranked_ids, relevant_ids):
    return round(sum(1 for i in ranked_ids[:5] if i in relevant_ids)/5, 4)


def validate_quality_parity(before_ranks: list, after_ranks: list,
                              relevant_ids: set, tolerance: float = 0.005) -> dict:
    """
    Prove quality is held constant after optimisation.
    Tolerance 0.005 = half a percent — within measurement noise.
    """
    b_ndcg = ndcg_at_5(before_ranks, relevant_ids)
    a_ndcg = ndcg_at_5(after_ranks,  relevant_ids)
    b_p5   = precision_at_5(before_ranks, relevant_ids)
    a_p5   = precision_at_5(after_ranks,  relevant_ids)
    ndcg_delta = round(abs(b_ndcg - a_ndcg), 4)
    p5_delta   = round(abs(b_p5   - a_p5),   4)
    return {
        "ndcg_before": b_ndcg, "ndcg_after": a_ndcg, "ndcg_delta": ndcg_delta,
        "p5_before":   b_p5,   "p5_after":   a_p5,   "p5_delta":   p5_delta,
        "quality_held_constant": ndcg_delta <= tolerance and p5_delta <= tolerance,
        "tolerance": tolerance,
    }
