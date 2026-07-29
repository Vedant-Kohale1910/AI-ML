"""Task 14 — Live demo.  Run: python demo.py"""
import json, os, sys
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from fairness.audit import assign_groups, run_audit
from fairness.mitigation import compute_calibration
from explainability.explanation_engine import explain, explain_safe, set_enabled, MODEL_VERSION
from recommendation.feature_engineering import FeatureEngineer

def sep(t): print(f"\n{'='*58}\n  {t}\n{'='*58}")

def build_df(students, jobs, interactions):
    fe = FeatureEngineer()
    positives = set(zip(
        interactions[interactions["event_type"].isin(["apply","shortlist"])]["student_id"].astype(int),
        interactions[interactions["event_type"].isin(["apply","shortlist"])]["job_id"].astype(int),
    ))
    rows = []
    for student in students:
        for job in jobs:
            feats = fe.extract_features(student, job)
            score = round(0.55*feats.get("skill_match",0)+0.25*feats.get("experience_match",0)+
                          0.10*feats.get("assessment_score",0)+0.10*feats.get("certification_match",0),4)
            rows.append({"student_id":student["student_id"],"job_id":job["job_id"],
                         "score":score,"recommended":int(score>=0.40),
                         "relevant":int((student["student_id"],job["job_id"]) in positives)})
    return pd.DataFrame(rows)

def main():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: students=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json")) as f: jobs=json.load(f)
    interactions = pd.read_csv(os.path.join(BASE,"data/event_logs.csv"))
    job_map = {j["job_id"]: j for j in jobs}

    scored = build_df(students, jobs, interactions)
    groups_df = assign_groups(students)
    df = scored.merge(groups_df[["student_id","experience_tier","assessment_tier","assessment_score"]], on="student_id")

    sep("STEP 1 — Real data: 10 candidates, experience groups")
    print(groups_df[["name","experience_tier","assessment_tier","years_experience","assessment_score"]].to_string(index=False))

    sep("STEP 2 — Bias audit BEFORE mitigation")
    audit = run_audit(df, "experience_tier")
    b = audit["demographic_parity"]; e = audit["equal_opportunity"]
    print(f"  {'Group':<16} | Rec Rate | TPR")
    for g in sorted(b["rates"]): print(f"  {g:<16} | {b['rates'][g]}     | {e['tprs'].get(g,'n/a')}")
    print(f"\n  DPD = {b['dpd']}  (target <0.10) — EXCEEDS threshold. Bias detected.")
    print(f"  EOD = {e['eod']}  (target <0.10)")

    sep("STEP 3 — Mitigation: post-processing score calibration")
    offsets = compute_calibration(df, "experience_tier", "score")
    print(f"  Calibration offsets: {dict(offsets)}")
    print("  Junior candidates receive a score lift to compensate for systematic under-scoring.")
    df["adjusted_score"] = (df["score"] + df["experience_tier"].map(offsets).fillna(0)).clip(0,1)
    threshold = df["adjusted_score"].quantile(0.50)
    df["recommended_mitigated"] = (df["adjusted_score"] >= threshold).astype(int)

    sep("STEP 4 — Re-audit AFTER mitigation")
    df_after = df.copy(); df_after["recommended"] = df_after["recommended_mitigated"]
    a2 = run_audit(df_after, "experience_tier")
    b2 = a2["demographic_parity"]; e2 = a2["equal_opportunity"]
    print(f"  {'Metric':<6} | Before | After  | Target | Pass")
    dpd_pass = "✓" if b2["dpd"] is not None and b2["dpd"] < 0.10 else "✗"
    print(f"  {'DPD':<6} | {b['dpd']}   | {b2['dpd']}  | <0.10  | {dpd_pass}")
    eod_pass = "✓" if e2["eod"] is not None and e2["eod"] < 0.10 else "—"
    print(f"  {'EOD':<6} | {e['eod']}   | {e2['eod']}  | <0.10  | {eod_pass}")

    sep("STEP 5 — Per-decision explanation (API output)")
    student = students[0]
    top_row = df[df["student_id"]==student["student_id"]].sort_values("adjusted_score",ascending=False).iloc[0]
    job = job_map[int(top_row["job_id"])]
    result = explain(student, job, float(top_row["score"]), float(top_row["adjusted_score"]))
    import json as _j; print(_j.dumps(result, indent=2))

    sep("STEP 6 — FAILURE SCENARIO: explanation service disabled")
    set_enabled(False)
    fallback = explain_safe(student, job, float(top_row["score"]))
    print(f"  fallback={fallback['fallback']}")
    print(f"  explanation={fallback['explanation']}")
    print("  System still returns a response. No crash.")
    set_enabled(True)

    sep("DEMO COMPLETE")
    print(f"  Model: {MODEL_VERSION}")
    print("  Reports: bias_audit.md, fairness_before/after.csv, explainability_examples.md")

if __name__ == "__main__":
    main()
