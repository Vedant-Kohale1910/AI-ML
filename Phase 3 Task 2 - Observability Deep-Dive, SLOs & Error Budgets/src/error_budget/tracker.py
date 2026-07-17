"""
Error Budget Tracker — tracks monthly downtime consumption and burn rate.

Error budget = (1 - availability_SLO) × minutes_in_month
             = 0.001 × 43,200 = 43.2 minutes / month

Burn rate: how fast the budget is being spent.
  burn_rate = 1 → on track to consume exactly the budget by end of month
  burn_rate = 2 → budget will be exhausted in half the month
"""

from datetime import datetime
from typing import Dict, List, Any, Tuple

from src.slo.definitions import ERROR_BUDGET, ErrorBudget


class ErrorBudgetTracker:
    def __init__(self, budget: ErrorBudget = ERROR_BUDGET):
        self.budget = budget
        self._incidents: List[Dict[str, Any]] = []

    # ── Recording ─────────────────────────────────────────────────────────────

    def record_incident(self, start: str, duration_minutes: float,
                        category: str, description: str) -> Dict[str, Any]:
        incident = {
            "id":                   len(self._incidents) + 1,
            "start":                start,
            "duration_minutes":     round(duration_minutes, 2),
            "category":             category,
            "description":          description,
            "recorded_at":          datetime.utcnow().isoformat(),
        }
        self._incidents.append(incident)
        return incident

    # ── Budget computations ───────────────────────────────────────────────────

    @property
    def used_minutes(self) -> float:
        return sum(i["duration_minutes"] for i in self._incidents)

    @property
    def status(self) -> Dict[str, Any]:
        base    = self.budget.remaining(self.used_minutes)
        br      = base["burn_rate"]

        health = (
            "CRITICAL — budget exhausted, freeze releases" if base["exhausted"]
            else "HIGH — budget >75% consumed" if base["pct_consumed"] >= 75
            else "ELEVATED — budget >50% consumed" if base["pct_consumed"] >= 50
            else "HEALTHY"
        )

        return {
            **base,
            "budget_health":   health,
            "total_incidents": len(self._incidents),
        }

    # ── Reporting ─────────────────────────────────────────────────────────────

    def report(self) -> str:
        s = self.status
        lines = [
            "ERROR BUDGET REPORT",
            "=" * 72,
            f"  SLO Target           : {self.budget.availability_target*100:.2f}% availability",
            f"  Monthly Budget       : {s['budget_minutes']:.1f} minutes",
            f"  Used This Period     : {s['used_minutes']:.2f} minutes",
            f"  Remaining            : {s['remaining_minutes']:.2f} minutes",
            f"  Burn Rate            : {s['burn_rate']:.2f}×  (1.0 = on track)",
            f"  % Consumed           : {s['pct_consumed']:.1f}%",
            f"  Budget Health        : {s['budget_health']}",
            f"  Incidents Recorded   : {s['total_incidents']}",
            "",
            "INCIDENT LOG:",
        ]
        if not self._incidents:
            lines.append("  (none)")
        else:
            for inc in self._incidents:
                lines.append(
                    f"  #{inc['id']:02d} [{inc['start']}] "
                    f"{inc['duration_minutes']:.1f} min — {inc['category']}: {inc['description']}"
                )
        return "\n".join(lines)

    def policy(self) -> Dict[str, Any]:
        """Return freeze/throttle policy based on current budget health."""
        pct = self.status["pct_consumed"]
        return {
            "freeze_releases":      pct >= 100,
            "throttle_experiments": pct >= 75,
            "accelerate_retrain":   pct >= 50,
            "pct_consumed":         pct,
            "recommendation": (
                "FREEZE all non-critical deploys; focus 100% on reliability"
                if pct >= 100
                else "HALT risky experiments; prioritise stability fixes"
                if pct >= 75
                else "REVIEW release cadence; retrain model if quality dropping"
                if pct >= 50
                else "Normal operations — budget healthy"
            ),
        }
