"""
Verifier — Stage E: "Deliberately induce the failure and confirm the
designed degradation actually happens." Also produces the metrics used
in verification_report.md and the baseline-vs-v1 comparison.
"""
from .event_joiner import EventJoiner


class LogVerifier:
    def __init__(self, all_events: list):
        self.events = all_events
        self.joiner = EventJoiner(all_events)

    # ---- Definition-of-Done checks ------------------------------------
    def check_position_logging(self):
        imps = [e for e in self.events if e["event_type"] == "impression"]
        return all(e.get("rank_position") is not None for e in imps) if imps else False

    def check_model_version_logging(self):
        imps = [e for e in self.events if e["event_type"] == "impression"]
        return all(e.get("model_version") for e in imps) if imps else False

    def check_joinability(self, threshold=0.99):
        return self.joiner.joinability_rate() >= threshold

    def run_all_checks(self):
        return {
            "position_logging_present": self.check_position_logging(),
            "model_version_logging_present": self.check_model_version_logging(),
            "outcomes_joinable_to_impressions": self.check_joinability(),
            "joinability_rate": self.joiner.joinability_rate(),
        }

    # ---- Funnel metrics --------------------------------------------------
    def funnel_metrics(self):
        journeys = self.joiner.build_journeys()
        n = len(journeys)
        clicks = sum(1 for j in journeys if j["click"])
        applies = sum(1 for j in journeys if j["apply"])
        shortlists = sum(1 for j in journeys if j["shortlist"])
        return {
            "impressions": n,
            "clicks": clicks,
            "applies": applies,
            "shortlists": shortlists,
            "ctr": round(clicks / n, 4) if n else 0,
            "apply_rate": round(applies / n, 4) if n else 0,
            "shortlist_rate": round(shortlists / n, 4) if n else 0,
        }

    # ---- Baseline vs improved comparison ---------------------------------
    def baseline_vs_v1(self):
        """Baseline = click-only logging (no position/model-version/apply/
        shortlist join). Improved (v1) = the full pipeline in this task."""
        journeys = self.joiner.build_journeys()
        n = len(journeys)
        clicks = sum(1 for j in journeys if j["click"])
        traceable_applies_baseline = 0  # baseline can't join apply->impression at all
        traceable_applies_v1 = sum(1 for j in journeys if j["apply"])
        return {
            "baseline": {
                "logs_position": False,
                "logs_model_version": False,
                "traces_apply_to_impression": False,
                "click_events_captured": clicks,
                "applies_traceable": traceable_applies_baseline,
            },
            "v1_this_task": {
                "logs_position": True,
                "logs_model_version": True,
                "traces_apply_to_impression": True,
                "click_events_captured": clicks,
                "applies_traceable": traceable_applies_v1,
                "of_total_impressions": n,
            },
        }

    # ---- Failure scenario ------------------------------------------------
    def failure_scenario_report(self, events_with_impressions_disabled: list):
        """Compare a run where impression logging was disabled: confirm
        apply/click events exist but CANNOT be traced back (joinability drops)."""
        j2 = EventJoiner(events_with_impressions_disabled)
        return {
            "impression_logging": "DISABLED",
            "outcome_events_still_fired": len(
                [e for e in events_with_impressions_disabled if e["event_type"] != "impression"]),
            "joinability_rate_with_impressions_disabled": j2.joinability_rate(),
            "expected_degradation": "joinability_rate drops to 0.0 — applies cannot be traced to any model/position",
            "degradation_confirmed": j2.joinability_rate() == 0.0,
        }
