"""
Offline Ranking Evaluation — Stage C
nDCG@k and MAP@k computed from scratch (no sklearn dependency needed).
"""
import numpy as np


def dcg(relevances: list, k: int) -> float:
    """Discounted Cumulative Gain at k."""
    rels = relevances[:k]
    return sum(r / np.log2(i + 2) for i, r in enumerate(rels))


def ndcg_at_k(ranked_relevances: list, k: int) -> float:
    """nDCG@k: DCG / ideal DCG."""
    ideal = sorted(ranked_relevances, reverse=True)
    idcg = dcg(ideal, k)
    if idcg == 0:
        return 0.0
    return round(dcg(ranked_relevances, k) / idcg, 4)


def average_precision(ranked_relevances: list, k: int) -> float:
    """Average Precision@k."""
    hits, score = 0, 0.0
    for i, r in enumerate(ranked_relevances[:k]):
        if r > 0:
            hits += 1
            score += hits / (i + 1)
    return round(score / max(hits, 1), 4)


def mean_ndcg(query_results: list, k: int = 10) -> float:
    """Mean nDCG@k over a list of relevance lists."""
    scores = [ndcg_at_k(r, k) for r in query_results]
    return round(np.mean(scores), 4) if scores else 0.0


def mean_ap(query_results: list, k: int = 10) -> float:
    """MAP@k over a list of relevance lists."""
    scores = [average_precision(r, k) for r in query_results]
    return round(np.mean(scores), 4) if scores else 0.0


def evaluate(query_results: dict, k: int = 5) -> dict:
    """
    query_results: {student_id: {"heuristic": [rel,...], "ltr": [rel,...]}}
    Returns aggregate metrics for both rankers.
    """
    h_lists = [v["heuristic"] for v in query_results.values()]
    l_lists = [v["ltr"]       for v in query_results.values()]
    return {
        "k": k,
        "heuristic": {"ndcg": mean_ndcg(h_lists, k), "map": mean_ap(h_lists, k)},
        "ltr":        {"ndcg": mean_ndcg(l_lists, k), "map": mean_ap(l_lists, k)},
    }
