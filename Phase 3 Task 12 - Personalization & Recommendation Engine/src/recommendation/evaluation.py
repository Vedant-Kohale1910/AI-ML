"""
evaluation.py — Precision@K, Coverage, Diversity, Latency vs baseline.
"""
import math


# ── Diversity ──────────────────────────────────────────────────────────────
def intra_list_diversity(recs: list, all_jobs: list) -> float:
    """
    Mean pairwise skill-set distance across recommended jobs.
    Higher = more diverse (less filter-bubble risk).
    """
    job_skills = {j["job_id"]: set(str(s).lower() for s in j["required_skills"])
                  for j in all_jobs}
    ids = [r["job_id"] for r in recs]
    if len(ids) < 2:
        return 1.0
    pairs, total = 0, 0.0
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = job_skills.get(ids[i], set()), job_skills.get(ids[j], set())
            union = a | b
            if union:
                jaccard = len(a & b) / len(union)
                total += 1 - jaccard   # distance = 1 - similarity
            pairs += 1
    return round(total / pairs, 4)


# ── Coverage ───────────────────────────────────────────────────────────────
def catalog_coverage(all_rec_job_ids: set, total_jobs: int) -> float:
    """% of the job catalog surfaced across ALL recommendation lists."""
    return round(len(all_rec_job_ids) / max(total_jobs, 1), 4)


# ── Precision@K ────────────────────────────────────────────────────────────
def precision_at_k(recs: list, relevant_ids: set, k: int) -> float:
    hits = sum(1 for r in recs[:k] if r["job_id"] in relevant_ids)
    return round(hits / k, 4)


# ── Baseline (popularity-only) ─────────────────────────────────────────────
def popularity_baseline(jobs: list, interactions, top_k=5):
    """
    Baseline: recommend the globally most-clicked jobs to every candidate.
    This is the pitfall the study guide calls 'popularity collapse'.
    """
    from collections import Counter
    clicks = interactions[interactions["event_type"] == "click"]
    counts = Counter(clicks["job_id"].tolist())
    sorted_jobs = sorted(jobs, key=lambda j: counts.get(j["job_id"], 0), reverse=True)
    return [{"job_id": j["job_id"], "title": j["title"]} for j in sorted_jobs[:top_k]]


# ── Aggregate eval ─────────────────────────────────────────────────────────
def evaluate_engine(students, jobs, interactions, rec_fn, baseline_fn, top_k=5):
    """
    Returns per-student metrics + aggregate comparison.
    rec_fn(student) -> (recs, latency_ms)
    baseline_fn() -> [job_id, ...]
    """
    import pandas as pd
    clicks = interactions[interactions["event_type"].isin(["click", "apply", "shortlist"])]

    baseline_recs = baseline_fn()
    baseline_job_ids = {r["job_id"] for r in baseline_recs}

    all_rec_ids_model = set()
    all_rec_ids_baseline = set()

    p_model, p_base, div_model, div_base, latencies = [], [], [], [], []

    for student in students:
        sid = student["student_id"]
        relevant = set(clicks[clicks["student_id"] == sid]["job_id"].tolist())
        if not relevant:
            continue

        recs, lat = rec_fn(student)
        latencies.append(lat)
        all_rec_ids_model.update(r["job_id"] for r in recs)
        all_rec_ids_baseline.update(baseline_job_ids)

        p_model.append(precision_at_k(recs, relevant, top_k))
        p_base.append(precision_at_k(
            [{"job_id": r["job_id"]} for r in baseline_recs], relevant, top_k))
        div_model.append(intra_list_diversity(recs, jobs))
        div_base.append(intra_list_diversity(
            [{"job_id": r["job_id"]} for r in baseline_recs], jobs))

    n = max(len(p_model), 1)
    return {
        "precision_at_k": {
            "k": top_k,
            "model": round(sum(p_model) / n, 4),
            "baseline": round(sum(p_base) / n, 4),
        },
        "diversity": {
            "model": round(sum(div_model) / n, 4),
            "baseline": round(sum(div_base) / n, 4),
        },
        "coverage": {
            "model": catalog_coverage(all_rec_ids_model, len(jobs)),
            "baseline": catalog_coverage(all_rec_ids_baseline, len(jobs)),
        },
        "latency_ms": {
            "p50": round(sorted(latencies)[len(latencies) // 2], 2) if latencies else 0,
            "p95": round(sorted(latencies)[int(len(latencies) * 0.95)], 2) if latencies else 0,
            "slo_ms": 200,
            "slo_met": all(l < 200 for l in latencies),
        },
    }
