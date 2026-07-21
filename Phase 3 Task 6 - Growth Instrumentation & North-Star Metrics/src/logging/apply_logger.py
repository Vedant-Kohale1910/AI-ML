"""Apply Logger — records when a student applies to a job."""
from .schema import OutcomeEvent


class ApplyLogger:
    def __init__(self, sink: list):
        self.sink = sink

    def log_apply(self, student_id, job_id, session_id):
        evt = OutcomeEvent(student_id=student_id, job_id=job_id,
                            session_id=session_id, event_type="apply")
        self.sink.append(evt.to_dict())
        return evt
