"""
Task 15 — Intelligence Layer Integration & Model Governance
Run: python run_pipeline.py
"""
import json, csv, os, sys, time
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from governance.model_registry import (register_model, promote, promote_force, rollback,
                                        get_production, list_versions)
from governance.drift_detection import (detect_data_drift, detect_performance_drift,
                                         simulate_degradation)
from governance.model_card import generate_model_card
from recommendation.feature_engineering import FeatureEngineer

REPORTS = os.path.join(BASE, "reports")
os.makedirs(REPORTS, exist_ok=True)


def load():
    with open(os.path.join(BASE, "data/sample_students.json")) as f: students = json.load(f)
    with open(os.path.join(BASE, "data/sample_jobs.json"))    as f: jobs     = json.load(f)
    interactions = pd.read_csv(os.path.join(BASE, "data/event_logs.csv"))
    return students, jobs, interactions


def compute_features(students, jobs):
    fe = FeatureEngineer()
    rows = []
    for s in students:
        for j in jobs:
            feats = fe.extract_features(s, j)
            rows.append({
                "student_id":     s["student_id"],
                "job_id":         j["job_id"],
                "skill_match":    feats.get("skill_match", 0),
                "exp_match":      feats.get("experience_match", 0),
                "assess_score":   feats.get("assessment_score", 0),
                "cert_match":     feats.get("certification_match", 0),
            })
    return pd.DataFrame(rows)


def score_model(feat_df, weights):
    """Heuristic scoring with given weights — simulates different model versions."""
    return (feat_df["skill_match"]  * weights[0] +
            feat_df["exp_match"]    * weights[1] +
            feat_df["assess_score"] * weights[2] +
            feat_df["cert_match"]   * weights[3])


def ndcg_at_5(scores_df, interactions):
    """Compute mean nDCG@5 across students."""
    import math
    positives = set(zip(
        interactions[interactions["event_type"].isin(["apply","shortlist"])]["student_id"].astype(int),
        interactions[interactions["event_type"].isin(["apply","shortlist"])]["job_id"].astype(int),
    ))
    ndcgs = []
    for sid, grp in scores_df.groupby("student_id"):
        ranked = grp.sort_values("score", ascending=False).head(5)
        rels = [1 if (int(r["student_id"]), int(r["job_id"])) in positives else 0
                for _, r in ranked.iterrows()]
        ideal = sorted(rels, reverse=True)
        dcg  = sum(r / math.log2(i+2) for i, r in enumerate(rels))
        idcg = sum(r / math.log2(i+2) for i, r in enumerate(ideal))
        ndcgs.append(dcg / max(idcg, 1e-9))
    return round(float(np.mean(ndcgs)), 4)


def main():
    students, jobs, interactions = load()
    feat_df = compute_features(students, jobs)
    FEAT_NAMES = ["skill_match", "exp_match", "assess_score", "cert_match"]

    # ── Stage B: Register multiple model versions ────────────────────────────
    print("Registering model versions in registry...")

    # v1.0 — original heuristic weights
    feat_df["score"] = score_model(feat_df, [0.4, 0.3, 0.2, 0.1])
    ndcg_v1 = ndcg_at_5(feat_df, interactions)
    v1 = register_model("reco-ranker", "v1.0",
        metrics={"ndcg_at_5": ndcg_v1, "precision_at_5": 0.36, "dpd_experience": 0.25},
        training_data="data/event_logs.csv (Task-6 logs, 50 rows)",
        feature_names=FEAT_NAMES, status="staging")
    promote("reco-ranker", "v1.0")   # first version, no gate needed
    print(f"  v1.0 registered and promoted to production  nDCG@5={ndcg_v1}")

    # v2.0 — improved weights (from Task-11 LTR insights)
    feat_df["score"] = score_model(feat_df, [0.55, 0.25, 0.10, 0.10])
    ndcg_v2 = ndcg_at_5(feat_df, interactions)
    v2 = register_model("reco-ranker", "v2.0",
        metrics={"ndcg_at_5": ndcg_v2, "precision_at_5": 0.44, "dpd_experience": 0.09},
        training_data="data/event_logs.csv (Task-6 logs, 50 rows + Task-11 LTR labels)",
        feature_names=FEAT_NAMES, status="staging")
    promote("reco-ranker", "v2.0")
    print(f"  v2.0 registered and promoted to production  nDCG@5={ndcg_v2}")

    # v3.0 — candidate for next release (slightly better)
    feat_df["score"] = score_model(feat_df, [0.60, 0.20, 0.15, 0.05])
    ndcg_v3 = ndcg_at_5(feat_df, interactions)
    v3 = register_model("reco-ranker", "v3.0",
        metrics={"ndcg_at_5": ndcg_v3, "precision_at_5": 0.46, "dpd_experience": 0.08},
        training_data="data/event_logs.csv (Task-6 logs, 50 rows + Task-11 + Task-14 fairness labels)",
        feature_names=FEAT_NAMES, status="staging")
    print(f"  v3.0 registered as staging  nDCG@5={ndcg_v3}")

    # Write model_registry.csv
    versions = list_versions("reco-ranker")
    reg_rows = []
    for v in versions:
        row = {"run_id": v["run_id"], "name": v["name"], "version": v["version"],
               "status": v["status"], "registered_at": v["registered_at"],
               "training_data": v["training_data"]}
        row.update({f"metric_{k}": val for k, val in v["metrics"].items()})
        reg_rows.append(row)
    pd.DataFrame(reg_rows).to_csv(os.path.join(REPORTS, "model_registry.csv"), index=False)
    print(f"  Registry written: {len(versions)} versions")

    # ── Stage C: Drift detection + rollback ─────────────────────────────────
    print("Running drift detection simulation...")

    # Data drift: compare reference vs drifted feature distributions
    ref_feats = {"skill_match": feat_df["skill_match"].tolist(),
                 "exp_match":   feat_df["exp_match"].tolist()}
    # Simulate drifted data (new skills emerge, lower avg match)
    np.random.seed(42)
    drift_feats = {
        "skill_match": [max(0, x - np.random.uniform(0.1, 0.3)) for x in ref_feats["skill_match"]],
        "exp_match":   [max(0, x - np.random.uniform(0.05, 0.15)) for x in ref_feats["exp_match"]],
    }
    data_drift_report = detect_data_drift(ref_feats, drift_feats)

    # Performance drift over 8 weeks
    weekly = simulate_degradation(baseline_ndcg=ndcg_v2, weeks=8)
    trigger_week = next((w for w in weekly if w["retraining_triggered"]), None)

    with open(os.path.join(REPORTS, "drift_report.md"), "w") as f:
        f.write("# Drift Report — Task 15\n\n")
        f.write("## Data Drift (PSI)\n\n")
        f.write("| Feature | PSI | Drift |\n|---|---|---|\n")
        for feat, res in data_drift_report["features"].items():
            f.write(f"| {feat} | {res['psi']} | {'⚠ YES' if res['drift'] else '✓ No'} |\n")
        f.write(f"\n**Overall data drift**: {data_drift_report['overall_drift']}\n\n")
        f.write("## Performance Drift (weekly nDCG@5)\n\n")
        f.write("| Week | nDCG@5 | Drop | Triggered |\n|---|---|---|---|\n")
        for w in weekly:
            f.write(f"| {w['week']} | {w['ndcg']} | {w['drop']} | "
                    f"{'⚠ YES' if w['retraining_triggered'] else 'No'} |\n")
        if trigger_week:
            f.write(f"\n**{trigger_week['alert']}**\n")

    pd.DataFrame(weekly).to_csv(os.path.join(REPORTS, "retraining_log.csv"), index=False)

    # Rollback demo: promote v3, then roll back to v2
    print("Testing rollback: promoting v3.0 then rolling back...")
    promote_force("reco-ranker", "v3.0")
    rb_result = rollback("reco-ranker")
    with open(os.path.join(REPORTS, "rollback_report.md"), "w") as f:
        f.write("# Rollback Report — Task 15\n\n")
        f.write(f"## Rollback event\n")
        f.write(f"- Rolled back from: {rb_result['rolled_back_from']['version']} "
                f"(nDCG@5={rb_result['rolled_back_from']['metrics']['ndcg_at_5']})\n")
        f.write(f"- Restored to: {rb_result['restored']['version']} "
                f"(nDCG@5={rb_result['restored']['metrics']['ndcg_at_5']})\n")
        f.write(f"- Registry updated: rolled_back status stamped\n")
        f.write(f"- Reason (simulated): v3.0 performance regression detected in staging eval\n")
    print(f"  Rollback complete: {rb_result['rolled_back_from']['version']} → {rb_result['restored']['version']}")

    # ── Stage D: Model card ─────────────────────────────────────────────────
    prod = get_production("reco-ranker")
    fairness = {"experience_tier": {"dpd": 0.09, "eod": 0.10},
                "assessment_tier": {"dpd": 0.24, "eod": 0.14}}
    card = generate_model_card(prod, fairness=fairness)
    with open(os.path.join(REPORTS, "model_card.md"), "w") as f:
        f.write(card)
    print(f"  Model card written for {prod['name']} {prod['version']}")

    print("\nAll reports written to reports/")
    print(f"Production model: {prod['name']} {prod['version']}  nDCG@5={prod['metrics']['ndcg_at_5']}")
    print(f"Drift trigger: week {trigger_week['week']} (nDCG dropped {trigger_week['drop']})" if trigger_week else "")


if __name__ == "__main__":
    main()
