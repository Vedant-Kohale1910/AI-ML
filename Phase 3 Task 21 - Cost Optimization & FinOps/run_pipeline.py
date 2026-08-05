"""Task 21 — Cost Optimization & FinOps
Run: python run_pipeline.py"""
import json, os, sys
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from finops.finops import (build_cost_model, quality_check, precompute_all,
                             set_cache_enabled, INR_PER_USD)

REPORTS = os.path.join(BASE, "reports")
os.makedirs(REPORTS, exist_ok=True)
DAILY_REQUESTS = 50000


def load():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: s=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: j=json.load(f)
    return s, j


def main():
    students, jobs = load()
    print(f"FinOps: {len(students)} candidates, {len(jobs)} jobs, {DAILY_REQUESTS:,} req/day")
    model = build_cost_model(students, jobs, DAILY_REQUESTS)
    quality = quality_check(students, jobs)
    b, a, s = model["before"], model["after"], model["savings"]

    rows = [
        {"metric":"cost_per_inference_usd","before":b["cost_per_inference_usd"],"after":a["cost_per_inference_usd"],"savings_pct":s["inference_cost_reduction_pct"]},
        {"metric":"cost_per_shortlist_inr","before":b["cost_per_shortlist_inr"],"after":a["cost_per_shortlist_inr"],"savings_pct":s["inference_cost_reduction_pct"]},
        {"metric":"cost_per_1000_inferences_usd","before":b["cost_per_1000_inf_usd"],"after":a["cost_per_1000_inf_usd"],"savings_pct":s["inference_cost_reduction_pct"]},
        {"metric":"daily_serving_usd","before":b["daily_serving_usd"],"after":a["daily_serving_usd"],"savings_pct":s["daily_serving_reduction_pct"]},
        {"metric":"avg_latency_ms","before":b["avg_latency_ms"],"after":a["avg_latency_ms"],"savings_pct":s["latency_reduction_pct"]},
        {"metric":"ndcg_at_5","before":quality["ndcg_before"],"after":quality["ndcg_after"],"savings_pct":0},
    ]
    pd.DataFrame(rows).to_csv(os.path.join(REPORTS,"before_after_cost.csv"), index=False)

    with open(os.path.join(REPORTS,"optimization_report.md"),"w") as f:
        f.write("# Optimization Report — Task 21\n\n")
        f.write("## Before vs After\n\n")
        f.write("| Metric | Before | After | Savings |\n|---|---|---|---|\n")
        f.write(f"| Cost/1000 inferences | ${b['cost_per_1000_inf_usd']:.6f} | ${a['cost_per_1000_inf_usd']:.6f} | {s['inference_cost_reduction_pct']}% |\n")
        f.write(f"| Cost/shortlist (INR) | ₹{b['cost_per_shortlist_inr']:.4f} | ₹{a['cost_per_shortlist_inr']:.4f} | {s['inference_cost_reduction_pct']}% |\n")
        f.write(f"| Daily serving | ${b['daily_serving_usd']:.4f} | ${a['daily_serving_usd']:.4f} | {s['daily_serving_reduction_pct']}% |\n")
        f.write(f"| Avg latency | {b['avg_latency_ms']:.4f}ms | {a['avg_latency_ms']:.4f}ms | {s['latency_reduction_pct']}% |\n")
        f.write(f"| nDCG@5 | {quality['ndcg_before']} | {quality['ndcg_after']} | {'HELD ✓' if quality['quality_held'] else 'DEGRADED ✗'} |\n")

    print(f"Cost/1000 inf: ${b['cost_per_1000_inf_usd']:.6f} → ${a['cost_per_1000_inf_usd']:.6f} ({s['inference_cost_reduction_pct']}%)")
    print(f"Daily serving: ${b['daily_serving_usd']:.4f} → ${a['daily_serving_usd']:.4f} ({s['daily_serving_reduction_pct']}%)")
    print(f"nDCG@5: {quality['ndcg_before']} → {quality['ndcg_after']} quality_held={quality['quality_held']}")
    print("Reports written to reports/")

if __name__ == "__main__":
    main()
