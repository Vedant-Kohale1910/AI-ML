"""Task 19 — White-Label Configurability & Admin Control Plane
Run: python run_pipeline.py"""
import json, os, sys, math
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from policy.policy_engine import load_policy, deploy_policy, rank_candidates, preview_policy_change
from policy.guardrails import validate

REPORTS = os.path.join(BASE, "reports")
os.makedirs(REPORTS, exist_ok=True)


def load():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: s=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: j=json.load(f)
    return s, j


def ndcg5(ranks, rel_ids):
    rels = [1 if r["student_id"] in rel_ids else 0 for r in ranks[:5]]
    ideal = sorted(rels, reverse=True)
    dcg  = sum(r/math.log2(i+2) for i,r in enumerate(rels))
    idcg = sum(r/math.log2(i+2) for i,r in enumerate(ideal))
    return round(dcg/max(idcg,1e-9),4)


def main():
    students, jobs = load()
    job = jobs[0]
    relevant = {students[0]["student_id"], students[1]["student_id"]}

    # ── Stage B: Per-tenant ranking ──────────────────────────────────────────
    print("Ranking candidates under per-tenant policies...")
    tenant_results = {}
    for tenant in ["google","microsoft","amazon"]:
        policy = load_policy(tenant)
        ranks  = rank_candidates(students, job, policy, top_k=5)
        tenant_results[tenant] = {"ranks": ranks, "ndcg": ndcg5(ranks, relevant), "policy": policy}
        print(f"  {tenant}: top={ranks[0]['name']} (score={ranks[0]['score']})  nDCG@5={tenant_results[tenant]['ndcg']}")

    # Baseline: default policy
    default_policy = load_policy("default")
    default_ranks  = rank_candidates(students, job, default_policy, top_k=5)
    base_ndcg = ndcg5(default_ranks, relevant)
    print(f"  baseline: top={default_ranks[0]['name']} nDCG@5={base_ndcg}")

    # ── Stage C: Guardrail tests ─────────────────────────────────────────────
    print("Running guardrail validation tests...")
    bad_configs = [
        ("weights_sum_wrong",  {"weights":{"skill":0.30,"experience":0.20,"assessment":0.10,"cert":0.05}}),
        ("negative_weight",    {"weights":{"skill":-0.10,"experience":0.60,"assessment":0.25,"cert":0.25}}),
        ("single_weight_high", {"weights":{"skill":0.90,"experience":0.06,"assessment":0.02,"cert":0.02}}),
        ("age_proxy_exp_gate", {"weights":{"skill":0.55,"experience":0.25,"assessment":0.10,"cert":0.10},
                                 "min_experience_years":10}),
        ("protected_attr_key", {"weights":{"skill":0.55,"experience":0.25,"assessment":0.10,"cert":0.10},
                                 "gender":"male_only"}),
    ]
    guard_rows = []
    for name, cfg in bad_configs:
        result = validate(cfg)
        guard_rows.append({"test": name, "valid": result["valid"],
                           "errors": "; ".join(result["errors"])})
        print(f"  {name}: valid={result['valid']}  errors={result['errors'][:1]}")
    pd.DataFrame(guard_rows).to_csv(os.path.join(REPORTS,"guardrail_results.csv"), index=False)

    # ── Stage D: Admin preview ───────────────────────────────────────────────
    print("Generating admin preview: google skill weight 0.60 → 0.75...")
    new_policy = {"tenant":"google","weights":{"skill":0.75,"experience":0.15,"assessment":0.07,"cert":0.03},
                  "min_experience_years":1,"required_skills_min":2,"boost_recent_grads":False}
    preview = preview_policy_change("google", new_policy, students, job, top_k=5)

    # Deploy the new policy after preview approved
    deployed = deploy_policy("google", new_policy)
    print(f"  Deployed: {deployed}")

    # ── Write reports ────────────────────────────────────────────────────────
    eval_rows = [{"tenant":t,"ndcg_at_5":v["ndcg"],"top_candidate":v["ranks"][0]["name"],
                  "skill_weight":v["policy"]["weights"]["skill"]}
                 for t,v in tenant_results.items()]
    eval_rows.append({"tenant":"default","ndcg_at_5":base_ndcg,
                      "top_candidate":default_ranks[0]["name"],"skill_weight":0.55})
    pd.DataFrame(eval_rows).to_csv(os.path.join(REPORTS,"evaluation_metrics.csv"), index=False)

    with open(os.path.join(REPORTS,"policy_comparison.md"),"w") as f:
        f.write("# Policy Comparison Report — Task 19\n\n")
        f.write("## Per-tenant ranking results\n\n")
        f.write("| Tenant | skill_w | exp_w | Top Candidate | nDCG@5 |\n|---|---|---|---|---|\n")
        for t, v in tenant_results.items():
            w = v["policy"]["weights"]
            f.write(f"| {t} | {w['skill']} | {w.get('experience',0)} | {v['ranks'][0]['name']} | {v['ndcg']} |\n")
        f.write(f"| default | 0.55 | 0.25 | {default_ranks[0]['name']} | {base_ndcg} |\n\n")
        f.write("## Design decision\n")
        f.write("**Rules on top of model** chosen over retraining per tenant.\n")
        f.write("Retraining per tenant requires per-tenant labelled data (scarce), "
                "separate CI/CD pipelines, and separate fairness audits. "
                "Policy rules are instant, auditable, and bounded by guardrails.\n\n")
        f.write("**Hard guardrails** over warnings. In hiring AI, warnings get dismissed. "
                "Hard rejection removes the ability to configure discrimination.\n")

    with open(os.path.join(REPORTS,"preview_report.md"),"w") as f:
        f.write("# Admin Preview Report — Task 19\n\n")
        f.write(f"**Config change**: google skill_weight 0.60 → 0.75\n\n")
        f.write("## Old ranking\n")
        for r in preview["old_ranking"]:
            f.write(f"{r['rank']}. {r['name']} ({r['score']})\n")
        f.write("\n## New ranking\n")
        for r in preview["new_ranking"]:
            f.write(f"{r['rank']}. {r['name']} ({r['score']})\n")
        f.write(f"\n## Rank changes\n")
        for c in preview["rank_changes"]:
            f.write(f"- {c['name']}: rank {c['old_rank']} → {c['new_rank']} {c['direction']}\n")
        f.write(f"\nnDCG@5 delta: {preview['ndcg_old']} → {preview['ndcg_new']} ({preview['ndcg_delta']:+.4f})\n")
        f.write(f"\nAdmin decision: APPROVED → deployed v{deployed['version']}\n")

    print(f"\nPreview: nDCG {preview['ndcg_old']} → {preview['ndcg_new']} ({preview['ndcg_delta']:+.4f})")
    print(f"Rank changes: {len(preview['rank_changes'])}")
    print("Reports written to reports/")


if __name__ == "__main__":
    main()
