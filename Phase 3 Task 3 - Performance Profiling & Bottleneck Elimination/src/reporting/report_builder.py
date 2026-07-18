"""
Report Builder  —  Task 3
Assembles the before/after comparison, cost estimates, and design rationale.
"""

from typing import Dict, List, Any
from src.profiler.pipeline_profiler import PipelineProfile


COST_PER_MS_PER_REQUEST = 0.0000023   # ₹ / ms / request
REQUESTS_PER_DAY        = 50_000


def cost_per_day(p95_ms: float) -> float:
    """Rough inference cost proportional to p95 latency."""
    return p95_ms * COST_PER_MS_PER_REQUEST * REQUESTS_PER_DAY


class ReportBuilder:
    def before_after(self, baseline: PipelineProfile, optimised: PipelineProfile,
                     strategy: str, quality_comparison: Dict[str, Any]) -> Dict[str, Any]:

        b_p95 = baseline.total_p95()
        o_p95 = optimised.total_p95()
        latency_reduction_pct = (b_p95 - o_p95) / b_p95 * 100 if b_p95 else 0

        b_cost = cost_per_day(b_p95)
        o_cost = cost_per_day(o_p95)

        return {
            "strategy": strategy,
            "latency": {
                "baseline_p95_ms":  round(b_p95, 1),
                "optimised_p95_ms": round(o_p95, 1),
                "reduction_ms":     round(b_p95 - o_p95, 1),
                "reduction_pct":    round(latency_reduction_pct, 1),
                "slo_target_ms":    500.0,
                "slo_met":          o_p95 <= 500.0,
            },
            "cost": {
                "baseline_inr_day":  round(b_cost,  2),
                "optimised_inr_day": round(o_cost,  2),
                "saving_inr_day":    round(b_cost - o_cost, 2),
                "saving_pct":        round((b_cost - o_cost) / b_cost * 100 if b_cost else 0, 1),
            },
            "quality": quality_comparison,
        }

    def print_profile_table(self, profile: PipelineProfile, title: str) -> None:
        rows = profile.report_rows()
        print(f"\n  {title}")
        print(f"  {'Stage':<20} {'p50':>8} {'p95':>8} {'p99':>8} {'%total':>8}  Bottleneck?")
        print(f"  {'-'*65}")
        for r in rows:
            flag = "  ← BOTTLENECK" if r["is_bottleneck"] else ""
            print(f"  {r['stage']:<20} {r['p50_ms']:>7.1f}ms {r['p95_ms']:>7.1f}ms "
                  f"{r['p99_ms']:>7.1f}ms {r['pct_of_total']:>7.1f}%{flag}")
        print(f"  {'─'*65}")
        print(f"  {'TOTAL (sum p95)':<20} {'':>8} {profile.total_p95():>7.1f}ms")

    def print_before_after(self, report: Dict[str, Any]) -> None:
        lat = report["latency"]
        cst = report["cost"]
        q   = report["quality"]

        print(f"\n  Strategy   : {report['strategy']}")
        print(f"\n  {'Metric':<30} {'Before':>12} {'After':>12} {'Change':>14}")
        print(f"  {'-'*70}")
        print(f"  {'p95 Latency (ms)':<30} {lat['baseline_p95_ms']:>12.1f} "
              f"{lat['optimised_p95_ms']:>12.1f} "
              f"{-lat['reduction_pct']:>13.1f}%")
        print(f"  {'Serving Cost (₹/day)':<30} {cst['baseline_inr_day']:>12.2f} "
              f"{cst['optimised_inr_day']:>12.2f} "
              f"{-cst['saving_pct']:>13.1f}%")

        print(f"\n  Quality Metrics (k=5, n=200 held-out queries):")
        for name, vals in q.get("metrics", {}).items():
            delta_str = f"{vals['delta']:+.4f}"
            ok_str    = "✓" if vals["within_tol"] else "✗ VIOLATION"
            print(f"    {name:<20} {vals['baseline']:>8.4f} → {vals['optimised']:>8.4f}  "
                  f"Δ {delta_str:>8}  {ok_str}")

        print(f"\n  SLO Met              : {'✓ YES' if lat['slo_met'] else '✗ NO'} "
              f"(target {lat['slo_target_ms']:.0f}ms, achieved {lat['optimised_p95_ms']:.1f}ms)")
        print(f"  Quality Acceptable   : {'✓ YES' if q['quality_acceptable'] else '✗ NO'}")
