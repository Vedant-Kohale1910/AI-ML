"""Shortlist Logger — records when a recruiter shortlists a candidate."""
from .schema import OutcomeEvent


class ShortlistLogger:
    def __init__(self, sink: list):
        self.sink = sink

    def log_shortlist(self, student_id, job_id, session_id, recruiter_id):
        evt = OutcomeEvent(student_id=student_id, job_id=job_id,
                            session_id=session_id, event_type="shortlist",
                            recruiter_id=recruiter_id)
        self.sink.append(evt.to_dict())
        return evt
