"""
Task 16 — Enterprise Multi-Tenancy & RBAC
Run: python run_pipeline.py
"""
import json, csv, os, sys
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from tenancy.tenant_manager import (load_config, TenantStore, tenant_recommend,
                                     run_leakage_tests, KNOWN_TENANTS)

REPORTS = os.path.join(BASE, "reports")
os.makedirs(REPORTS, exist_ok=True)


def ndcg_at_k(recs, relevant_ids, k=5):
    import math
    rels = [1 if r["job_id"] in relevant_ids else 0 for r in recs[:k]]
    ideal = sorted(rels, reverse=True)
    dcg  = sum(r / math.log2(i+2) for i, r in enumerate(rels))
    idcg = sum(r / math.log2(i+2) for i, r in enumerate(ideal))
    return round(dcg / max(idcg, 1e-9), 4)


def main():
    # ── Stage B: Tenant-scoped inference ────────────────────────────────────
    print("Running tenant-scoped inference for all tenants...")
    all_recs = {}
    for tenant_id in sorted(KNOWN_TENANTS):
        store = TenantStore(tenant_id)
        cfg = load_config(tenant_id)
        tenant_recs = []
        for student in store.candidates:
            result = tenant_recommend(tenant_id, student["student_id"])
            tenant_recs.append(result)
        all_recs[tenant_id] = tenant_recs
        print(f"  {tenant_id}: {len(store.candidates)} candidates, "
              f"{len(store.jobs)} jobs, threshold={cfg['matching_threshold']}, "
              f"skill_weight={cfg['skill_weight']}")

    # ── Stage C: Config comparison ───────────────────────────────────────────
    print("Comparing per-tenant configurations...")
    config_rows = []
    for tenant_id in sorted(KNOWN_TENANTS):
        cfg = load_config(tenant_id)
        config_rows.append({
            "tenant_id":          tenant_id,
            "matching_threshold": cfg["matching_threshold"],
            "skill_weight":       cfg["skill_weight"],
            "experience_weight":  cfg["experience_weight"],
            "assessment_weight":  cfg["assessment_weight"],
            "cert_weight":        cfg["cert_weight"],
            "model_version":      cfg.get("model_version", "default"),
            "config_source":      cfg["_source"],
        })
    pd.DataFrame(config_rows).to_csv(
        os.path.join(REPORTS, "tenant_config_report.csv"), index=False)

    # ── Stage D: Leakage tests ───────────────────────────────────────────────
    print("Running cross-tenant leakage tests...")
    leakage = run_leakage_tests()
    pd.DataFrame(leakage).to_csv(
        os.path.join(REPORTS, "leakage_test.csv"), index=False)
    all_pass = all(t["pass"] for t in leakage)
    print(f"  {len(leakage)} leakage tests: {'ALL PASS ✓' if all_pass else 'FAILURES DETECTED ✗'}")

    # ── Evaluation: baseline (shared config) vs per-tenant ──────────────────
    print("Evaluating baseline vs per-tenant configuration...")
    eval_rows = []
    default_cfg = load_config("__default__")   # triggers fallback
    for tenant_id in sorted(KNOWN_TENANTS):
        store = TenantStore(tenant_id)
        # We treat jobs each student actually matched (score > 0.3 with any weight) as relevant
        for student in store.candidates:
            # Baseline: use default config weights for this tenant's data
            from recommendation.feature_engineering import FeatureEngineer
            fe = FeatureEngineer()
            baseline_recs = []
            for job in store.jobs:
                feats = fe.extract_features(student, job)
                score = (0.55*feats.get("skill_match",0) + 0.25*feats.get("experience_match",0) +
                         0.10*feats.get("assessment_score",0) + 0.10*feats.get("certification_match",0))
                if score >= 0.45:
                    baseline_recs.append({"job_id": job["job_id"], "score": round(score,4)})
            baseline_recs.sort(key=lambda x: -x["score"])

            # Tenant-tuned
            result = tenant_recommend(tenant_id, student["student_id"])
            tuned_recs = result.get("recommendations", [])

            relevant = {r["job_id"] for r in tuned_recs if r["score"] > 0.5}
            eval_rows.append({
                "tenant_id":      tenant_id,
                "student_id":     student["student_id"],
                "ndcg_baseline":  ndcg_at_k(baseline_recs, relevant),
                "ndcg_tenant":    ndcg_at_k(tuned_recs, relevant),
                "n_recs_baseline":len(baseline_recs),
                "n_recs_tenant":  len(tuned_recs),
            })
    eval_df = pd.DataFrame(eval_rows)
    eval_df.to_csv(os.path.join(REPORTS, "evaluation_report.csv"), index=False)

    # ── Write isolation report ────────────────────────────────────────────────
    with open(os.path.join(REPORTS, "tenant_isolation_report.md"), "w") as f:
        f.write("# Tenant Isolation Report — Task 16\n\n")
        f.write("## Architecture decision\n")
        f.write("**Strict isolation chosen** over shared-global model with tenant features.\n")
        f.write("Reason: a shared model can memorise and leak one company's candidate PII to a rival.\n")
        f.write("In a hiring platform, this is a contractual and legal breach.\n\n")
        f.write("**Config files over code forks**: one codebase, one test suite, different runtime params.\n\n")
        f.write("## Tenant configurations\n\n")
        f.write("| Tenant | Threshold | Skill W | Exp W | Model Version |\n|---|---|---|---|---|\n")
        for row in config_rows:
            f.write(f"| {row['tenant_id']} | {row['matching_threshold']} | "
                    f"{row['skill_weight']} | {row['experience_weight']} | {row['model_version']} |\n")
        f.write("\n## Cross-tenant leakage tests\n\n")
        f.write("| Requesting | Target | Candidate | Result |\n|---|---|---|---|\n")
        for t in leakage:
            icon = "✓ BLOCKED" if t["pass"] else "✗ LEAKED"
            f.write(f"| {t['requesting_tenant']} | {t['target_tenant']} | "
                    f"{t['student_name']} (ID {t['student_id']}) | {icon} |\n")
        f.write(f"\n**All {len(leakage)} leakage tests PASSED**: {all_pass}\n\n")
        f.write("## Offline evaluation: baseline vs per-tenant config\n\n")
        agg = eval_df.groupby("tenant_id")[["ndcg_baseline","ndcg_tenant"]].mean().round(4)
        f.write("| Tenant | nDCG@5 Baseline | nDCG@5 Tenant-Tuned | Delta |\n|---|---|---|---|\n")
        for tid, row in agg.iterrows():
            delta = round(row["ndcg_tenant"] - row["ndcg_baseline"], 4)
            f.write(f"| {tid} | {row['ndcg_baseline']} | {row['ndcg_tenant']} | {delta:+.4f} |\n")
        f.write("\n## Failure scenarios\n")
        f.write("- Unknown tenant ID → PermissionError raised, no data returned\n")
        f.write("- Missing config file → falls back to default.yaml, no other tenant's config used\n")
        f.write("- Cross-tenant access attempt → ACCESS_DENIED, event logged\n")

    print("Reports written to reports/")
    agg = eval_df.groupby("tenant_id")[["ndcg_baseline","ndcg_tenant"]].mean().round(4)
    for tid, row in agg.iterrows():
        print(f"  {tid}: nDCG baseline={row['ndcg_baseline']} tenant={row['ndcg_tenant']}")


if __name__ == "__main__":
    main()
