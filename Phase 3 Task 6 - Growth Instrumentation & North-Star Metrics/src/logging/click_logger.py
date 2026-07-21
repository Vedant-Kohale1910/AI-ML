"""Click Logger — records when a student clicks a recommended job."""
from .schema import OutcomeEvent


class ClickLogger:
    def __init__(self, sink: list):
        self.sink = sink

    def log_click(self, student_id, job_id, session_id):
        evt = OutcomeEvent(student_id=student_id, job_id=job_id,
                            session_id=session_id, event_type="click")
        self.sink.append(evt.to_dict())
        return evt
