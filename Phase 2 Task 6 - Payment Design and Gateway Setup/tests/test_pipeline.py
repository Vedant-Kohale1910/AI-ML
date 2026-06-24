"""
test_pipeline.py
----------------
Unit tests covering the full pipeline:
- data generation produces the expected shape / columns
- feature engineering computes sensible values
- baseline heuristic scores are in range
- the model loads and produces predictions

Run: pytest tests/ -v
"""

import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.utils.data_generator import (
    generate_students, generate_jobs, compute_ground_truth, ALL_SKILLS
)
from src.features.feature_engineering import build_pair_features
from src.models.baseline import heuristic_score, evaluate_baseline


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def small_students():
    # Use enough students that we get at least a handful of positive pairs
    return generate_students(n=100)


@pytest.fixture(scope="module")
def small_jobs():
    return generate_jobs(n=20)


@pytest.fixture(scope="module")
def small_labels(small_students, small_jobs):
    return compute_ground_truth(small_students, small_jobs)


@pytest.fixture(scope="module")
def small_features(small_students, small_jobs, small_labels):
    return build_pair_features(small_students, small_jobs, small_labels)


# ── data generation tests ─────────────────────────────────────────────────────

class TestDataGeneration:
    def test_student_count(self, small_students):
        assert len(small_students) == 100

    def test_student_has_all_skills(self, small_students):
        for skill in ALL_SKILLS:
            assert skill in small_students.columns, f"Missing skill column: {skill}"

    def test_skill_scores_in_range(self, small_students):
        for skill in ALL_SKILLS:
            scores = small_students[skill]
            assert scores.min() >= 0, f"{skill} has score < 0"
            assert scores.max() <= 100, f"{skill} has score > 100"

    def test_cgpa_range(self, small_students):
        assert small_students["cgpa"].between(5.0, 10.0).all()

    def test_job_count(self, small_jobs):
        assert len(small_jobs) == 20

    def test_job_has_required_skills(self, small_jobs):
        for _, row in small_jobs.iterrows():
            skills = json.loads(row["required_skills"])
            assert isinstance(skills, list)
            assert len(skills) > 0

    def test_ground_truth_label_binary(self, small_labels):
        assert set(small_labels["label"].unique()).issubset({0, 1})

    def test_ground_truth_has_positives(self, small_labels):
        # with 30 students and 10 jobs there should be at least a few positives
        assert small_labels["label"].sum() > 0, "No positive labels — check thresholds"

    def test_pair_count(self, small_students, small_jobs, small_labels):
        expected_pairs = len(small_students) * len(small_jobs)
        assert len(small_labels) == expected_pairs


# ── feature engineering tests ─────────────────────────────────────────────────

class TestFeatureEngineering:
    def test_feature_columns_present(self, small_features):
        expected = [
            "skill_overlap_ratio", "mean_score_on_required", "score_gap_mean",
            "skills_below_threshold", "nice_to_have_overlap", "cgpa_gap",
            "max_skill_score", "avg_skill_score", "graduation_recency",
            "required_skills_count", "min_score_threshold",
        ]
        for col in expected:
            assert col in small_features.columns, f"Missing feature: {col}"

    def test_overlap_ratio_in_0_to_1(self, small_features):
        r = small_features["skill_overlap_ratio"]
        assert r.min() >= 0.0
        assert r.max() <= 1.0

    def test_no_nulls(self, small_features):
        assert small_features.isnull().sum().sum() == 0, "Feature matrix has NaNs"

    def test_label_preserved(self, small_features, small_labels):
        assert set(small_features["label"].unique()).issubset({0, 1})

    def test_score_gap_sign(self, small_features):
        # for perfect matches overlap should be 1.0 and gap >= 0
        perfect = small_features[small_features["skill_overlap_ratio"] == 1.0]
        if len(perfect) > 0:
            assert (perfect["score_gap_mean"] >= 0).all()


# ── baseline model tests ──────────────────────────────────────────────────────

class TestBaseline:
    def test_heuristic_score_range(self, small_features):
        scores = small_features.apply(heuristic_score, axis=1)
        assert scores.min() >= 0
        assert scores.max() <= 100

    def test_high_overlap_gets_high_score(self):
        perfect_row = pd.Series({
            "skill_overlap_ratio": 1.0,
            "mean_score_on_required": 90.0,
            "cgpa_gap": 2.0,
            "skills_below_threshold": 0,
            "nice_to_have_overlap": 1.0,
        })
        assert heuristic_score(perfect_row) >= 80

    def test_zero_overlap_gets_low_score(self):
        bad_row = pd.Series({
            "skill_overlap_ratio": 0.0,
            "mean_score_on_required": 30.0,
            "cgpa_gap": -1.0,
            "skills_below_threshold": 5,
            "nice_to_have_overlap": 0.0,
        })
        assert heuristic_score(bad_row) < 40

    def test_evaluate_baseline_returns_metrics(self, small_features):
        if len(small_features) < 10:
            pytest.skip("Too few samples for metric evaluation")
        if small_features["label"].sum() == 0:
            pytest.skip("No positive labels in small fixture — increase fixture size")
        metrics, _ = evaluate_baseline(small_features)
        for key in ["precision", "recall", "f1", "roc_auc", "false_positive_rate"]:
            assert key in metrics
            assert 0.0 <= metrics[key] <= 1.0, f"{key} out of range"

    def test_metrics_not_all_zero(self, small_features):
        if len(small_features) < 10:
            pytest.skip("Too few samples")
        if small_features["label"].sum() == 0:
            pytest.skip("No positive labels in small fixture — increase fixture size")
        metrics, _ = evaluate_baseline(small_features)
        total = sum(metrics[k] for k in ["precision", "recall", "roc_auc"])
        assert total > 0, "All metrics are zero — something is wrong"


# ── integration smoke test ────────────────────────────────────────────────────

class TestIntegration:
    def test_full_pipeline_runs(self):
        students = generate_students(n=20)
        jobs = generate_jobs(n=5)
        labels = compute_ground_truth(students, jobs)
        features = build_pair_features(students, jobs, labels)

        assert len(features) > 0
        assert "label" in features.columns

        scores = features.apply(heuristic_score, axis=1)
        assert len(scores) == len(features)
        assert scores.notna().all()
