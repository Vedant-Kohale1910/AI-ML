"""Task 19 — Live demo.  Run: python demo.py"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from policy.policy_engine import load_policy, deploy_policy, rank_candidates, preview_policy_change
from policy.guardrails import validate

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def main():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: students=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: jobs=json.load(f)
    job = jobs[0]

    sep("STEP 1 — Per-tenant configs (same code, different policies)")
    for tenant in ["google","microsoft","amazon"]:
        p = load_policy(tenant)
        print(f"  {tenant:<12}: skill={p['weights']['skill']}  exp={p['weights']['experience']}  "
              f"min_exp={p.get('min_experience_years',0)}yr  boost_grads={p.get('boost_recent_grads',False)}")
    print("\n  All tenants run the same scoring function. Only policy JSON differs.")

    sep("STEP 2 — Same job, different rankings per tenant")
    print(f"  Job: {job['title']} ({job['company']})\n")
    for tenant in ["google","microsoft"]:
        p = load_policy(tenant)
        ranks = rank_candidates(students, job, p, top_k=3)
        print(f"  [{tenant}]")
        for r in ranks:
            print(f"    #{r['rank']}  {r['name']:<18}  score={r['score']}")
        print()

    sep("STEP 3 — Guardrail: 5 bad configs rejected")
    bad = [
        ("weights_sum_wrong",  {"weights":{"skill":0.30,"experience":0.20,"assessment":0.10,"cert":0.05}}),
        ("negative_weight",    {"weights":{"skill":-0.10,"experience":0.60,"assessment":0.25,"cert":0.25}}),
        ("single_weight_90%",  {"weights":{"skill":0.90,"experience":0.06,"assessment":0.02,"cert":0.02}}),
        ("exp_gate_10yr",      {"weights":{"skill":0.55,"experience":0.25,"assessment":0.10,"cert":0.10},"min_experience_years":10}),
        ("gender_filter",      {"weights":{"skill":0.55,"experience":0.25,"assessment":0.10,"cert":0.10},"gender":"male_only"}),
    ]
    for name, cfg in bad:
        r = validate(cfg)
        print(f"  {name:<22}: valid={r['valid']}  → {r['errors'][0][:70]}")

    sep("STEP 4 — Admin preview: google skill 0.60 → 0.75 (before deploying)")
    new_policy = {"tenant":"google",
                  "weights":{"skill":0.75,"experience":0.15,"assessment":0.07,"cert":0.03},
                  "min_experience_years":1,"required_skills_min":2,"boost_recent_grads":False}
    preview = preview_policy_change("google", new_policy, students, job, top_k=5)
    print(f"  Old top-3:")
    for r in preview["old_ranking"][:3]: print(f"    #{r['rank']} {r['name']:<18} {r['score']}")
    print(f"  New top-3 (after skill weight increase):")
    for r in preview["new_ranking"][:3]: print(f"    #{r['rank']} {r['name']:<18} {r['score']}")
    if preview["rank_changes"]:
        print(f"\n  Rank changes:")
        for c in preview["rank_changes"]:
            print(f"    {c['name']}: {c['old_rank']} → {c['new_rank']} {c['direction']}")
    else:
        print(f"\n  No rank order changes — but scores changed (skill-dominant candidates boosted).")
    print(f"  nDCG@5 delta: {preview['ndcg_delta']:+.4f}")
    print(f"  safe_to_deploy: {preview['safe_to_deploy']}")

    sep("STEP 5 — Admin approves: deploy new policy live")
    result = deploy_policy("google", new_policy)
    print(f"  Status:  {result['status']}")
    print(f"  Version: {result['version']}")
    ranks_after = rank_candidates(students, job, new_policy, top_k=3)
    print(f"  Live rankings under new policy:")
    for r in ranks_after:
        print(f"    #{r['rank']} {r['name']:<18} {r['score']}")

    sep("STEP 6 — FAILURE SCENARIO: deploy bad config → guardrail blocks")
    bad_policy = {"tenant":"google",
                  "weights":{"skill":0.95,"experience":0.03,"assessment":0.01,"cert":0.01},
                  "min_experience_years":15}
    try:
        deploy_policy("google", bad_policy)
    except ValueError as e:
        print(f"  ValueError raised — deployment BLOCKED:")
        print(f"  {str(e)[:200]}")
        print("\n  Old policy remains active. No broken config reaches users.")

    sep("DEMO COMPLETE")
    print("  Reports: policy_comparison.md, guardrail_results.csv,")
    print("           preview_report.md, evaluation_metrics.csv")

if __name__ == "__main__":
    main()
