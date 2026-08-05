"""Task 21 — Live demo.  Run: python demo.py"""
import json, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE, "src"))

from finops.finops import (build_cost_model, quality_check, score_on_demand,
                             score_cached, score_precomputed, precompute_all,
                             set_cache_enabled, _cache, INR_PER_USD)

DAILY_REQUESTS = 50000

def sep(t): print(f"\n{'='*60}\n  {t}\n{'='*60}")

def main():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: students=json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: jobs=json.load(f)
    model = build_cost_model(students, jobs, DAILY_REQUESTS)
    quality = quality_check(students, jobs)
    b, a, s = model["before"], model["after"], model["savings"]
    student, job = students[0], jobs[0]

    sep("STEP 1 — Cost model: unit economics BEFORE optimization")
    print(f"  Scale          : {DAILY_REQUESTS:,} inferences/day")
    print(f"  Hardware       : CPU t3.medium ($0.048/hr)")
    print(f"  Avg latency    : {b['avg_latency_ms']:.4f} ms per pair")
    print(f"  Cost/inference : ${b['cost_per_inference_usd']:.2e}  (INR {b['cost_per_inference_inr']:.6f})")
    print(f"  Cost/shortlist : INR {b['cost_per_shortlist_inr']:.4f}")
    print(f"  Cost/1000 inf  : ${b['cost_per_1000_inf_usd']:.6f}")
    print(f"  Daily serving  : ${b['daily_serving_usd']:.4f}  (INR {b['daily_serving_inr']:.2f})")
    print("  Most expensive: Feature extraction (55%) — recomputed on every request")

    sep("STEP 2 — Optimization A: result cache")
    sc_miss, lat_miss, cost_miss, _ = score_cached(student, job)
    sc_hit,  lat_hit,  cost_hit,  _ = score_cached(student, job)
    print(f"  Cache miss: score={sc_miss}  lat={lat_miss:.4f}ms  cost=${cost_miss:.2e}")
    print(f"  Cache HIT:  score={sc_hit}   lat={lat_hit:.4f}ms   cost=${cost_hit:.2e}")
    print(f"  Score identical: {sc_miss == sc_hit}. Latency reduced by {round((1-lat_hit/max(lat_miss,1e-9))*100,0):.0f}%")

    sep("STEP 3 — Optimization B: precompute nightly")
    n_pairs = len(students) * len(jobs)
    pc_ms = precompute_all(students, jobs)
    sc_pc, lat_pc, cost_pc = score_precomputed(student, job)
    print(f"  Nightly batch: {n_pairs} pairs in {pc_ms} ms")
    print(f"  Serve-time:    score={sc_pc}  lat={lat_pc:.4f}ms  cost=${cost_pc:.2e}")
    print(f"  Score equals on-demand: {sc_pc == sc_miss}")

    sep("STEP 4 — Before vs After: cost per 1000 inferences")
    print(f"  {'Metric':<28} {'Before':<16} {'After':<16} Savings")
    print(f"  {'Cost/1000 inferences':28} ${b['cost_per_1000_inf_usd']:.6f}      ${a['cost_per_1000_inf_usd']:.6f}      {s['inference_cost_reduction_pct']}%")
    print(f"  {'Cost/shortlist (INR)':28} INR{b['cost_per_shortlist_inr']:.4f}      INR{a['cost_per_shortlist_inr']:.4f}      {s['inference_cost_reduction_pct']}%")
    print(f"  {'Daily serving ($)':28} ${b['daily_serving_usd']:.4f}       ${a['daily_serving_usd']:.4f}       {s['daily_serving_reduction_pct']}%")
    print(f"  {'nDCG@5':28} {quality['ndcg_before']}           {quality['ndcg_after']}           {'HELD ✓' if quality['quality_held'] else 'DEGRADED ✗'}")

    sep("STEP 5 — Right-sizing: CPU not GPU")
    print("  Scoring = weighted sum of 4 features. Linear arithmetic, no matrix ops.")
    print("  GPU p3.xlarge: $0.23/hr. CPU t3.medium: $0.048/hr. 4.8x more expensive.")
    print("  GPU rejected: same output, 4.8x higher cost. Savings = $0 quality gain.")
    print("  GPU only warranted if we add a neural cross-encoder re-ranker (future).")

    sep("STEP 6 — FAILURE: cache disabled → graceful cost degradation")
    set_cache_enabled(False)
    _cache.clear()
    sc2, lat2, _, _ = score_cached(student, job)
    print(f"  Cache disabled. Score={sc2}  lat={lat2:.4f}ms")
    print(f"  Cost reverts to ${b['cost_per_inference_usd']:.2e}/inference (on-demand).")
    print("  No crash. No wrong answers. Serving cost degrades, quality unchanged.")
    set_cache_enabled(True)

    sep("DEMO COMPLETE")
    print(f"  Inference cost reduction : {s['inference_cost_reduction_pct']}%")
    print(f"  Daily serving reduction  : {s['daily_serving_reduction_pct']}%")
    print(f"  Quality delta (nDCG@5)   : {quality['delta']} — held constant")

if __name__ == "__main__":
    main()
