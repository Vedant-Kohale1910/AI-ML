"""
policy_engine.py — Stages B + D
Loads per-tenant policy, scores candidates, generates admin preview.
"""
import json
import os
import sys
import math
import time

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "../.."))

from recommendation.feature_engineering import FeatureEngineer
from policy.guardrails import validate

CONFIGS_DIR = os.path.join(BASE, "../../configs")
_fe = FeatureEngineer()

# In-memory live policy store {tenant: policy_dict}
_live_policies = {}


# ── Policy load / save ────────────────────────────────────────────────────────

def load_policy(tenant: str) -> dict:
    if tenant in _live_policies:
        return _live_policies[tenant]
    path = os.path.join(CONFIGS_DIR, f"{tenant}_policy.json")
    if not os.path.exists(path):
        path = os.path.join(CONFIGS_DIR, "default_policy.json")
    with open(path) as f:
        policy = json.load(f)
    _live_policies[tenant] = policy
    return policy


def deploy_policy(tenant: str, new_policy: dict) -> dict:
    """Validate then deploy. Raises ValueError if guardrails fail."""
    result = validate(new_policy)
    if not result["valid"]:
        raise ValueError(f"Policy rejected by guardrails:\n" +
                         "\n".join(f"  ✗ {e}" for e in result["errors"]))
    new_policy["version"] = str(round(time.time()))
    new_policy["deployed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _live_policies[tenant] = new_policy
    return {"status": "deployed", "tenant": tenant,
            "version": new_policy["version"], "warnings": result["warnings"]}


# ── Scoring ───────────────────────────────────────────────────────────────────

def score_candidate(student: dict, job: dict, policy: dict) -> float:
    feats = _fe.extract_features(student, job)
    w = policy.get("weights", {})
    score = (w.get("skill", 0.55)       * feats.get("skill_match", 0) +
             w.get("experience", 0.25)  * feats.get("experience_match", 0) +
             w.get("assessment", 0.10)  * feats.get("assessment_score", 0) +
             w.get("cert", 0.10)        * feats.get("certification_match", 0))
    # Apply hard gates (min experience, min skills)
    if student.get("years_experience", 0) < policy.get("min_experience_years", 0):
        score *= 0.5
    if len(student.get("verified_skills", [])) < policy.get("required_skills_min", 0):
        score *= 0.5
    # Boost recent grads (1 yr or less) if configured
    if policy.get("boost_recent_grads") and student.get("years_experience", 0) <= 1:
        score = min(1.0, score * 1.15)
    return round(score, 4)


def rank_candidates(students: list, job: dict, policy: dict, top_k: int = 5) -> list:
    scored = []
    for s in students:
        sc = score_candidate(s, job, policy)
        scored.append({"student_id": s["student_id"], "name": s["name"],
                        "skills": s["verified_skills"], "score": sc})
    scored.sort(key=lambda x: -x["score"])
    for i, r in enumerate(scored, 1):
        r["rank"] = i
    return scored[:top_k]


# ── Admin preview ─────────────────────────────────────────────────────────────

def preview_policy_change(tenant: str, new_policy: dict,
                           students: list, job: dict, top_k: int = 5) -> dict:
    """
    Show old vs new ranking BEFORE deploying.
    Returns diff for admin approval.
    """
    guard = validate(new_policy)
    if not guard["valid"]:
        return {"preview_blocked": True, "errors": guard["errors"]}

    old_policy = load_policy(tenant)
    old_ranks  = rank_candidates(students, job, old_policy, top_k)
    new_ranks  = rank_candidates(students, job, new_policy, top_k)

    # Compute rank changes
    old_pos = {r["student_id"]: r["rank"] for r in old_ranks}
    new_pos = {r["student_id"]: r["rank"] for r in new_ranks}
    all_ids = set(old_pos) | set(new_pos)

    changes = []
    for sid in all_ids:
        o = old_pos.get(sid, "out")
        n = new_pos.get(sid, "out")
        if o != n:
            name = next((s["name"] for s in students if s["student_id"] == sid), str(sid))
            changes.append({"name": name, "old_rank": o, "new_rank": n,
                            "direction": "↑ improved" if (isinstance(n,int) and isinstance(o,int) and n < o)
                                        else "↓ dropped" if (isinstance(n,int) and isinstance(o,int) and n > o)
                                        else "new/removed"})

    # nDCG delta
    def ndcg(ranks, rel_ids):
        rels = [1 if r["student_id"] in rel_ids else 0 for r in ranks]
        ideal = sorted(rels, reverse=True)
        dcg  = sum(r/math.log2(i+2) for i,r in enumerate(rels))
        idcg = sum(r/math.log2(i+2) for i,r in enumerate(ideal))
        return round(dcg/max(idcg,1e-9),4)

    rel = {students[0]["student_id"], students[1]["student_id"]}  # top 2 as ground truth
    old_ndcg = ndcg(old_ranks, rel)
    new_ndcg = ndcg(new_ranks, rel)

    return {
        "preview_blocked": False,
        "tenant":          tenant,
        "old_policy_weights": old_policy["weights"],
        "new_policy_weights": new_policy["weights"],
        "old_ranking":     [{"rank":r["rank"],"name":r["name"],"score":r["score"]} for r in old_ranks],
        "new_ranking":     [{"rank":r["rank"],"name":r["name"],"score":r["score"]} for r in new_ranks],
        "rank_changes":    changes,
        "ndcg_old":        old_ndcg,
        "ndcg_new":        new_ndcg,
        "ndcg_delta":      round(new_ndcg - old_ndcg, 4),
        "warnings":        guard["warnings"],
        "safe_to_deploy":  True,
    }
