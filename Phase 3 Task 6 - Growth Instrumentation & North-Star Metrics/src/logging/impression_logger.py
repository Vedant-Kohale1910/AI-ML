"""Impression Logger — records every ranked list shown to a student.
This is Position + Model-Version logging (Stage C of the study guide)."""
from .schema import ImpressionEvent


class ImpressionLogger:
    def __init__(self, sink: list, enabled: bool = True):
        self.sink = sink          # in-memory sink; swap for DB/Kafka in prod
        self.enabled = enabled    # toggled off to simulate the failure scenario

    def log_ranked_list(self, student_id, session_id, ranked_jobs, model_version):
        """ranked_jobs: list of dicts with job_id, score, rank (already ranked)."""
        if not self.enabled:
            return []  # <-- failure mode: nothing gets logged
        events = []
        for job in ranked_jobs:
            evt = ImpressionEvent(
                student_id=student_id,
                job_id=job["job_id"],
                session_id=session_id,
                model_version=model_version,
                rank_position=job["rank"],
                score=job["score"],
            )
            self.sink.append(evt.to_dict())
            events.append(evt)
        return events
