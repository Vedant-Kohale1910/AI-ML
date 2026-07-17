"""
Alert Engine — evaluates SLO checks and fires alerts.

Severity levels:
  WARNING  — SLO approaching breach (burn rate 2×)
  CRITICAL — SLO breached now
  PAGE     — degenerate output or availability < 99 %
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


SEVERITY_ORDER = {"INFO": 0, "WARNING": 1, "CRITICAL": 2, "PAGE": 3}


@dataclass
class Alert:
    severity:    str         # INFO / WARNING / CRITICAL / PAGE
    category:    str         # latency | availability | quality | distribution | error_budget
    title:       str
    detail:      str
    value:       float
    threshold:   float
    fired_at:    str = field(default_factory=lambda: datetime.utcnow().isoformat())
    resolved:    bool = False
    owner:       str = "ML-Ops"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity":  self.severity,
            "category":  self.category,
            "title":     self.title,
            "detail":    self.detail,
            "value":     self.value,
            "threshold": self.threshold,
            "fired_at":  self.fired_at,
            "resolved":  self.resolved,
            "owner":     self.owner,
        }


class AlertEngine:
    """Evaluate SLO check results and emit alerts."""

    def __init__(self):
        self.history: List[Alert] = []

    # ── Latency alerts ────────────────────────────────────────────────────────

    def _latency_alert(self, check: Dict[str, Any]) -> Optional[Alert]:
        if check["pass"]:
            return None
        p95 = check["p95_ms"]
        target = check["p95_target"]
        overage_pct = (p95 - target) / target * 100

        severity = "PAGE" if overage_pct > 100 else "CRITICAL" if overage_pct > 50 else "WARNING"
        return Alert(
            severity  = severity,
            category  = "latency",
            title     = f"[{severity}] Inference p95 latency SLO breach",
            detail    = (f"p95={p95:.0f}ms exceeds {target:.0f}ms target "
                        f"by {overage_pct:.0f}%. Recommendation requests degraded."),
            value     = p95,
            threshold = target,
        )

    # ── Availability alerts ───────────────────────────────────────────────────

    def _availability_alert(self, check: Dict[str, Any]) -> Optional[Alert]:
        if check["pass"]:
            return None
        avail  = check["availability"]
        target = check["target"]
        severity = "PAGE" if avail < 0.990 else "CRITICAL"
        return Alert(
            severity  = severity,
            category  = "availability",
            title     = f"[{severity}] Availability SLO breach",
            detail    = (f"Current availability {avail*100:.3f}% is below "
                        f"{target*100:.3f}% SLO. Error budget burning fast."),
            value     = avail,
            threshold = target,
        )

    # ── Quality alerts ────────────────────────────────────────────────────────

    def _quality_alert(self, check: Dict[str, Any]) -> Optional[Alert]:
        if check["pass"]:
            return None
        return Alert(
            severity  = "CRITICAL",
            category  = "quality",
            title     = "[CRITICAL] Prediction quality SLO breach",
            detail    = f"Quality violation: {check['reason']}",
            value     = check["f1"],
            threshold = 0.825,
        )

    # ── Degenerate-output alert ───────────────────────────────────────────────

    def _distribution_alert(self, check: Dict[str, Any]) -> Optional[Alert]:
        if check["pass"]:
            return None
        return Alert(
            severity  = "PAGE",
            category  = "distribution",
            title     = "[PAGE] DEGENERATE MODEL OUTPUT DETECTED",
            detail    = (f"Score std={check['std']:.4f}, range={check['range']:.4f}. "
                        f"Model may be returning constant scores. Immediate investigation required."),
            value     = check["std"],
            threshold = 0.05,
            owner     = "ML-Ops + On-Call",
        )

    # ── Error budget alert ────────────────────────────────────────────────────

    def _budget_alert(self, budget_status: Dict[str, Any]) -> Optional[Alert]:
        pct = budget_status["pct_consumed"]
        if pct < 50:
            return None
        severity = "PAGE" if budget_status["exhausted"] else (
            "CRITICAL" if pct >= 75 else "WARNING"
        )
        return Alert(
            severity  = severity,
            category  = "error_budget",
            title     = f"[{severity}] Error budget {pct:.0f}% consumed",
            detail    = (
                f"Budget exhausted — freeze non-critical deployments."
                if budget_status["exhausted"]
                else f"{pct:.0f}% of monthly error budget used. "
                     f"{budget_status['remaining_minutes']:.1f} min remaining."
            ),
            value     = pct,
            threshold = 50.0,
        )

    # ── Main entry ────────────────────────────────────────────────────────────

    def evaluate(self, slo_result: Dict[str, Any],
                 budget_status: Optional[Dict[str, Any]] = None) -> List[Alert]:
        fired: List[Alert] = []
        checks = slo_result.get("checks", {})

        for fn, key in [
            (self._latency_alert,      "latency"),
            (self._availability_alert, "availability"),
            (self._quality_alert,      "prediction_quality"),
            (self._distribution_alert, "score_distribution"),
        ]:
            if key in checks:
                a = fn(checks[key])
                if a:
                    fired.append(a)

        if budget_status:
            a = self._budget_alert(budget_status)
            if a:
                fired.append(a)

        self.history.extend(fired)
        fired.sort(key=lambda a: SEVERITY_ORDER.get(a.severity, 0), reverse=True)
        return fired

    def summary(self) -> Dict[str, Any]:
        sev_counts = {"INFO": 0, "WARNING": 0, "CRITICAL": 0, "PAGE": 0}
        for a in self.history:
            sev_counts[a.severity] = sev_counts.get(a.severity, 0) + 1
        return {"total_alerts": len(self.history), "by_severity": sev_counts,
                "recent": [a.to_dict() for a in self.history[-5:]]}
