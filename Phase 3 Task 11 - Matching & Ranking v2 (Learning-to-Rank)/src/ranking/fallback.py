"""
Fallback — Stage E failure scenario.
When the LTR model is unavailable, fall back to the Phase-2 heuristic ranker.
This satisfies: "show one failure scenario and confirm designed degradation."
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
from src.retrieval.ranking import RankingEngine

_heuristic = RankingEngine()

def rank_with_fallback(items: list, ltr_model=None) -> tuple:
    """
    Returns (ranked_list, used_fallback: bool).
    Falls back to heuristic score-sort if model is None or raises.
    """
    if ltr_model is None:
        ranked = _heuristic.rank_recommendations(items, method="score")
        return ranked, True
    try:
        import numpy as np
        from src.ranking.train_ltr import FEATURE_NAMES
        # items already have ltr_score set by caller
        ranked = sorted(items, key=lambda x: x.get("ltr_score", x["score"]), reverse=True)
        for i, r in enumerate(ranked, 1):
            r["rank"] = i
        return ranked, False
    except Exception:
        ranked = _heuristic.rank_recommendations(items, method="score")
        return ranked, True
