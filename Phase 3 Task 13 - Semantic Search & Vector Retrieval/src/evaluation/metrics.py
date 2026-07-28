"""
evaluation.py — nDCG@K, MAP@K, Precision@K for search quality.
Also builds a labelled eval set from real interaction logs.
"""
import math
import numpy as np
import pandas as pd


def _dcg(rels, k):
    return sum(r / math.log2(i + 2) for i, r in enumerate(rels[:k]))

def ndcg_at_k(ranked_ids, relevant_ids, k):
    rels = [1 if i in relevant_ids else 0 for i in ranked_ids[:k]]
    ideal = sorted(rels, reverse=True)
    idcg = _dcg(ideal, k)
    return round(_dcg(rels, k) / max(idcg, 1e-9), 4)

def precision_at_k(ranked_ids, relevant_ids, k):
    hits = sum(1 for i in ranked_ids[:k] if i in relevant_ids)
    return round(hits / k, 4)

def average_precision(ranked_ids, relevant_ids, k):
    hits, score = 0, 0.0
    for i, did in enumerate(ranked_ids[:k]):
        if did in relevant_ids:
            hits += 1
            score += hits / (i + 1)
    return round(score / max(hits, 1), 4)


def build_labelled_eval(interactions: pd.DataFrame, students: list, jobs: list):
    """
    Derive query→relevant_doc labels from real clicks/applies/shortlists.
    Query = job title (what a recruiter would search for).
    Relevant docs = student_ids who clicked/applied/were shortlisted.
    """
    pos = interactions[interactions["event_type"].isin(["click", "apply", "shortlist"])]
    job_map  = {j["job_id"]: j for j in jobs}
    eval_set = []
    for jid, grp in pos.groupby("job_id"):
        job = job_map.get(int(jid))
        if not job:
            continue
        relevant_students = set(int(s) for s in grp["student_id"].unique())
        eval_set.append({
            "query":             job["title"],
            "query_type":        "job_title",
            "relevant_ids":      relevant_students,
            "job_id":            job["job_id"],
        })
    return eval_set


def evaluate_search(eval_set, search_fn, all_ids, k=5):
    """
    search_fn(query) -> (ranked_ids, ...)
    Returns mean nDCG@k, MAP@k, Precision@k.
    """
    ndcgs, aps, precs = [], [], []
    for item in eval_set:
        ids, *_ = search_fn(item["query"])
        rel = item["relevant_ids"]
        ndcgs.append(ndcg_at_k(ids, rel, k))
        aps.append(average_precision(ids, rel, k))
        precs.append(precision_at_k(ids, rel, k))
    return {
        "ndcg":      round(np.mean(ndcgs), 4) if ndcgs else 0,
        "map":       round(np.mean(aps),   4) if aps   else 0,
        "precision": round(np.mean(precs), 4) if precs else 0,
        "n_queries": len(eval_set),
    }
