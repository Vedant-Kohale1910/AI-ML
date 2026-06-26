"""
Matching model for PlaceMux — computes a skill-overlap based match score
between a student profile and a job posting.

This is the core engine that Task 8's spend-quality guardrail sits on top of.
I kept it simple intentionally: a weighted Jaccard similarity that rewards
matching the required skills and gives partial credit for extras.
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path


def _normalise(skill_str: str) -> set:
    """Clean up a comma-separated skill string into a lowercase set."""
    if not isinstance(skill_str, str) or not skill_str.strip():
        return set()
    return {s.strip().lower() for s in skill_str.split(",") if s.strip()}


def compute_match_score(student_skills: str, job_required_skills: str) -> dict:
    """
    Compute how well a student matches a job based on skills.

    The logic here is straightforward:
    - matched_skills  = skills the student has AND the job wants
    - missing_skills  = skills the job wants that the student lacks
    - extra_skills    = student skills not required (nice to have, but don't penalise)

    Score = (matched / total_required) * 100

    Returns a dict with score + breakdown, so the caller can always explain
    why the student got that number (no black box).
    """
    student_set = _normalise(student_skills)
    required_set = _normalise(job_required_skills)

    if not required_set:
        return {
            "match_score": 0,
            "matched_skills": [],
            "missing_skills": [],
            "extra_skills": list(student_set),
        }

    matched = student_set & required_set
    missing = required_set - student_set
    extra = student_set - required_set

    # simple coverage ratio — easy to explain, easy to verify
    score = round((len(matched) / len(required_set)) * 100, 1)

    return {
        "match_score": score,
        "matched_skills": sorted(matched),
        "missing_skills": sorted(missing),
        "extra_skills": sorted(extra),
    }


class MatchingModel:
    """
    Wraps the compute_match_score function into a serialisable object so we
    can pickle it and load it from the API without re-running data setup.
    """

    def __init__(self, students_df: pd.DataFrame, jobs_df: pd.DataFrame):
        self.students_df = students_df.copy()
        self.jobs_df = jobs_df.copy()
        self._build_index()

    def _build_index(self):
        self._students = {
            row["student_id"]: row for _, row in self.students_df.iterrows()
        }
        self._jobs = {
            row["job_id"]: row for _, row in self.jobs_df.iterrows()
        }

    def predict(self, student_id: int, job_id: int) -> dict:
        """Given IDs, look up both rows and return the full match result."""
        if student_id not in self._students:
            raise ValueError(f"student_id {student_id} not found")
        if job_id not in self._jobs:
            raise ValueError(f"job_id {job_id} not found")

        student = self._students[student_id]
        job = self._jobs[job_id]

        result = compute_match_score(student["skills"], job["required_skills"])
        result["student_id"] = student_id
        result["job_id"] = job_id
        result["student_name"] = student["name"]
        result["job_title"] = job["title"]
        result["company"] = job["company"]
        result["application_fee"] = job["application_fee"]

        return result

    def save(self, path: str):
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"Model saved to {path}")

    @staticmethod
    def load(path: str) -> "MatchingModel":
        with open(path, "rb") as f:
            model = pickle.load(f)
        return model


if __name__ == "__main__":
    base = Path(__file__).parent.parent / "data"
    students = pd.read_csv(base / "students.csv")
    jobs = pd.read_csv(base / "jobs.csv")

    model = MatchingModel(students, jobs)
    model.save(Path(__file__).parent / "matching_model.pkl")

    # quick sanity check
    result = model.predict(1, 1)
    print(f"\nQuick test — Student 1 vs Job 1:")
    print(f"  Score      : {result['match_score']}%")
    print(f"  Matched    : {result['matched_skills']}")
    print(f"  Missing    : {result['missing_skills']}")
