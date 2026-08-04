"""
pilot_runner.py — Task 20: Enterprise Readiness Integration & Pilot Dry-Run

Integrates capabilities from Tasks 6-19:
  Task 6/11  → logging + LTR-style scoring
  Task 12    → two-sided recommendation
  Task 13    → semantic (LSA) search
  Task 14    → fairness audit
  Task 15    → model versioning
  Task 16/19 → tenant policy + guardrails
  Task 17    → rate-limited scoring
  Task 18    → identity-scoped personalization

Acceptance criteria (agreed with Google before pilot):
  Precision@5 ≥ 0.60
  nDCG@5     ≥ 0.70
  DPD        < 0.15
  Latency p95 < 200 ms
"""
import json, math, time, os, sys
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "../.."))

from recommendation.feature_engineering import FeatureEngineer

TENANT = "google"
MODEL_VERSION = "pilot-v1.0"

ACCEPTANCE = {
    "precision_at_5": 0.60,
    "ndcg_at_5":      0.70,
    "dpd":            0.15,
    "latency_p95_ms": 200,
}

_fe = FeatureEngineer()
_pilot_enabled = True


def _score(student, job, weights):
    feats = _fe.extract_features(student, job)
    return round(
        weights["skill"]   * feats.get("skill_match", 0) +
        weights["exp"]     * feats.get("experience_match", 0) +
        weights["assess"]  * feats.get("assessment_score", 0) +
        weights["cert"]    * feats.get("certification_match", 0), 4)


def _ndcg(ranked_ids, relevant_ids, k=5):
    rels = [1 if i in relevant_ids else 0 for i in ranked_ids[:k]]
    ideal = sorted(rels, reverse=True)
    dcg  = sum(r/math.log2(i+2) for i,r in enumerate(rels))
    idcg = sum(r/math.log2(i+2) for i,r in enumerate(ideal))
    return round(dcg/max(idcg,1e-9), 4)


def _precision(ranked_ids, relevant_ids, k=5):
    return round(sum(1 for i in ranked_ids[:k] if i in relevant_ids)/k, 4)


def run_pilot(students, jobs, policy_weights=None):
    """Run end-to-end pilot. Returns per-job recommendation + latency data."""
    if not _pilot_enabled:
        return None, "PILOT_UNAVAILABLE"

    weights = policy_weights or {"skill":0.60,"exp":0.25,"assess":0.10,"cert":0.05}
    results, latencies = [], []

    for job in jobs:
        t0 = time.perf_counter()
        scored = []
        for student in students:
            sc = _score(student, job, weights)
            scored.append({"student_id": student["student_id"],
                            "name": student["name"],
                            "skills": student["verified_skills"],
                            "score": sc})
        scored.sort(key=lambda x: -x["score"])
        top5 = scored[:5]
        lat = round((time.perf_counter() - t0) * 1000, 2)
        latencies.append(lat)

        # Plain-English explanation for rank-1 candidate
        top = top5[0]
        job_req = set(s.lower() for s in job["required_skills"])
        cand_skills = set(s.lower() for s in top["skills"])
        matched = sorted(job_req & cand_skills)
        explanation = (f"Skills matched: {', '.join(matched)}" if matched
                       else "Partial skill overlap — strongest available match")

        results.append({
            "job_id":        job["job_id"],
            "job_title":     job["title"],
            "top5":          top5,
            "top1_name":     top["name"],
            "top1_score":    top["score"],
            "top1_explanation": explanation,
            "latency_ms":    lat,
            "model_version": MODEL_VERSION,
        })

    return results, latencies


def quality_metrics(pilot_results, students):
    """Compute Precision@5 and nDCG@5 using assessment_score≥0.85 as proxy for relevant."""
    smap = {s["student_id"]: s for s in students}
    relevant_ids = {s["student_id"] for s in students
                    if s["assessment_score"] >= 0.85}

    precs, ndcgs = [], []
    for r in pilot_results:
        ranked = [x["student_id"] for x in r["top5"]]
        precs.append(_precision(ranked, relevant_ids))
        ndcgs.append(_ndcg(ranked, relevant_ids))

    return {
        "precision_at_5": round(np.mean(precs), 4),
        "ndcg_at_5":      round(np.mean(ndcgs), 4),
        "n_jobs":         len(pilot_results),
    }


def fairness_audit(students, pilot_results):
    """DPD across experience tiers: junior (<2yr) vs senior (≥2yr)."""
    junior_ids = {s["student_id"] for s in students if s["years_experience"] < 2}
    senior_ids = {s["student_id"] for s in students if s["years_experience"] >= 2}

    jr_top5_counts, sr_top5_counts, n_jobs = 0, 0, len(pilot_results)
    for r in pilot_results:
        top5_ids = {c["student_id"] for c in r["top5"]}
        jr_top5_counts += len(top5_ids & junior_ids)
        sr_top5_counts += len(top5_ids & senior_ids)

    # Rate = fraction of group that appears in top-5 recommendations (averaged over jobs)
    jr_rate = round(jr_top5_counts / max(len(junior_ids) * n_jobs, 1), 4)
    sr_rate = round(sr_top5_counts / max(len(senior_ids) * n_jobs, 1), 4)
    dpd = round(abs(jr_rate - sr_rate), 4)
    return {
        "junior_rec_rate": jr_rate, "senior_rec_rate": sr_rate,
        "dpd": dpd, "dpd_pass": dpd < ACCEPTANCE["dpd"],
        "n_junior": len(junior_ids), "n_senior": len(senior_ids),
    }


def latency_report(latencies):
    lats = sorted(latencies)
    return {
        "p50_ms":  round(lats[len(lats)//2], 2),
        "p95_ms":  round(lats[int(len(lats)*0.95)], 2),
        "max_ms":  round(max(lats), 2),
        "slo_pass": max(lats) < ACCEPTANCE["latency_p95_ms"],
    }


def acceptance_check(quality, fairness, latency):
    checks = {
        "precision_at_5": (quality["precision_at_5"], "≥", ACCEPTANCE["precision_at_5"],
                           quality["precision_at_5"] >= ACCEPTANCE["precision_at_5"]),
        "ndcg_at_5":      (quality["ndcg_at_5"],      "≥", ACCEPTANCE["ndcg_at_5"],
                           quality["ndcg_at_5"]      >= ACCEPTANCE["ndcg_at_5"]),
        "dpd":            (fairness["dpd"],            "<", ACCEPTANCE["dpd"],
                           fairness["dpd"]            <  ACCEPTANCE["dpd"]),
        "latency_p95_ms": (latency["p95_ms"],          "<", ACCEPTANCE["latency_p95_ms"],
                           latency["p95_ms"]          <  ACCEPTANCE["latency_p95_ms"]),
    }
    all_pass = all(v[3] for v in checks.values())
    return checks, all_pass


def remediation_list(quality, fairness, latency):
    items = []
    if quality["precision_at_5"] < ACCEPTANCE["precision_at_5"]:
        items.append({
            "issue": f"Precision@5={quality['precision_at_5']} below target {ACCEPTANCE['precision_at_5']}",
            "root_cause": "Domain shift: Google's specialised roles (Robotics, Chip Design) "
                          "use vocabulary absent from training data.",
            "remedy": "Collect 500+ Google-specific interaction logs; retrain embedding layer "
                      "with domain vocabulary expansion.",
            "priority": "HIGH", "owner": "AI/ML Engineer",
        })
    if fairness["dpd"] >= ACCEPTANCE["dpd"]:
        items.append({
            "issue": f"DPD={fairness['dpd']} exceeds target {ACCEPTANCE['dpd']}",
            "root_cause": "Junior candidates systematically under-ranked due to experience weight.",
            "remedy": "Apply post-processing IPS calibration (Task-14 mitigation) "
                      "with Google's specific experience distribution.",
            "priority": "HIGH", "owner": "AI/ML Engineer + Compliance",
        })
    if latency["p95_ms"] >= ACCEPTANCE["latency_p95_ms"]:
        items.append({
            "issue": f"Latency p95={latency['p95_ms']}ms above {ACCEPTANCE['latency_p95_ms']}ms",
            "root_cause": "Scoring 30 candidates × 12 jobs sequentially.",
            "remedy": "Vectorise scoring with numpy batch; add FAISS pre-filter for top-50 retrieval.",
            "priority": "MEDIUM", "owner": "Platform Engineer",
        })
    # Always include proactive items
    items.append({
        "issue": "Cold-start: new roles without prior interaction data",
        "root_cause": "No historical shortlists for Chip Designer, Robotics Engineer.",
        "remedy": "Use org-level signals from similar roles (Task-18 org scope) "
                  "as warm-start until 20+ interactions collected.",
        "priority": "MEDIUM", "owner": "AI/ML Engineer",
    })
    items.append({
        "issue": "Online validation not yet run",
        "root_cause": "Pilot is dry-run only — no live recruiter interactions measured.",
        "remedy": "Run 2-week shadow-mode A/B test (Task-17 API) logging recruiter click-through. "
                  "Gate production launch on CTR ≥ 20%.",
        "priority": "HIGH", "owner": "Product + AI/ML Engineer",
    })
    return items


def set_enabled(state: bool):
    global _pilot_enabled
    _pilot_enabled = state
