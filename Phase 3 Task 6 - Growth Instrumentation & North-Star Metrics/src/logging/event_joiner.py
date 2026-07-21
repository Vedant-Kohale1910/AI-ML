"""
Event Joiner — Stage E requirement:
"Show a real ranked impression and trace it to the outcome event."

Joins impression events to click/apply/shortlist events using the
join key (student_id, job_id, session_id).
"""
from collections import defaultdict


class EventJoiner:
    def __init__(self, all_events: list):
        self.events = all_events

    def _key(self, e):
        return (e["student_id"], e["job_id"], e["session_id"])

    def build_journeys(self):
        """Return one journey dict per (student, job, session) impression,
        with any click/apply/shortlist attached — or explicit None if missing."""
        impressions = [e for e in self.events if e["event_type"] == "impression"]
        outcomes_by_key = defaultdict(list)
        for e in self.events:
            if e["event_type"] != "impression":
                outcomes_by_key[self._key(e)].append(e)

        journeys = []
        for imp in impressions:
            k = self._key(imp)
            outcomes = outcomes_by_key.get(k, [])
            journey = {
                "student_id": imp["student_id"],
                "job_id": imp["job_id"],
                "session_id": imp["session_id"],
                "model_version": imp["model_version"],
                "rank_position": imp["rank_position"],
                "score": imp["score"],
                "impression_ts": imp["timestamp"],
                "click": next((o for o in outcomes if o["event_type"] == "click"), None),
                "apply": next((o for o in outcomes if o["event_type"] == "apply"), None),
                "shortlist": next((o for o in outcomes if o["event_type"] == "shortlist"), None),
            }
            journeys.append(journey)
        return journeys

    def trace(self, student_id, job_id, session_id):
        """Trace one specific impression -> full outcome chain (for the demo)."""
        for j in self.build_journeys():
            if (j["student_id"], j["job_id"], j["session_id"]) == (student_id, job_id, session_id):
                return j
        return None

    def joinability_rate(self):
        """% of outcome events (click/apply/shortlist) that could be joined
        back to a logged impression. This is the core Stage D metric."""
        outcomes = [e for e in self.events if e["event_type"] != "impression"]
        impression_keys = {self._key(e) for e in self.events if e["event_type"] == "impression"}
        if not outcomes:
            return 1.0
        joined = sum(1 for o in outcomes if self._key(o) in impression_keys)
        return round(joined / len(outcomes), 4)
