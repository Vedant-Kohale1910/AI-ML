"""
feature_engineering.py
-----------------------
Turns raw student + job CSVs into a feature matrix we can train on.

Each row in the output represents one (student, job) pair.
The features capture the "signal" a recruiter or matching algorithm
would naturally care about: skill overlap, score gaps, and context.

Run directly: python src/features/feature_engineering.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# so we can import sibling packages when running as a script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

RAW_DIR = os.path.join(os.path.dirname(__file__), "../../data/raw")
PROCESSED_DIR = os.path.join(os.path.dirname(__file__), "../../data/processed")

# skills we actually use as features (same list as the generator)
ALL_SKILLS = [
    "Python", "SQL", "Machine Learning", "Deep Learning", "NLP",
    "Data Analysis", "Statistics", "Docker", "Git", "REST APIs",
    "Java", "JavaScript", "React", "Node.js", "Cloud (AWS/GCP/Azure)",
    "Spark", "Tableau", "Excel", "Communication", "Problem Solving",
]


def load_raw_data():
    students = pd.read_csv(os.path.join(RAW_DIR, "students.csv"))
    jobs = pd.read_csv(os.path.join(RAW_DIR, "jobs.csv"))
    labels = pd.read_csv(os.path.join(RAW_DIR, "ground_truth.csv"))
    return students, jobs, labels


def build_pair_features(
    students: pd.DataFrame,
    jobs: pd.DataFrame,
    labels: pd.DataFrame,
) -> pd.DataFrame:
    """
    For each (student, job) pair in the labels table, compute:

    - skill_overlap_ratio       : fraction of required skills where score >= threshold
    - mean_score_on_required    : average student score across required skills
    - score_gap_mean            : average (score – threshold) across required skills
                                  (negative means student is below the bar)
    - skills_below_threshold    : count of required skills where student falls short
    - nice_to_have_overlap      : fraction of nice-to-have skills the student has (>=50)
    - cgpa_gap                  : student CGPA minus job minimum CGPA
    - max_skill_score           : student's single highest score (proxy for depth)
    - avg_skill_score           : student's average across ALL skills
    - graduation_recency        : years since graduation (fresher vs experienced)

    These are the kinds of signals a human recruiter thinks about. No leakage —
    we never use the label itself to compute a feature.
    """
    student_lookup = students.set_index("student_id")
    job_lookup = jobs.set_index("job_id")

    feature_rows = []

    for _, row in labels.iterrows():
        sid = row["student_id"]
        jid = row["job_id"]

        if sid not in student_lookup.index or jid not in job_lookup.index:
            continue

        s = student_lookup.loc[sid]
        j = job_lookup.loc[jid]

        required = json.loads(j["required_skills"])
        nice = json.loads(j["nice_to_have_skills"])
        threshold = j["min_score_threshold"]

        # ── required skill features ──────────────────────────────────────────
        req_scores = [s.get(skill, 0) for skill in required if skill in s.index]

        skill_overlap_ratio = (
            sum(1 for sc in req_scores if sc >= threshold) / len(req_scores)
            if req_scores else 0.0
        )
        mean_score_on_required = float(np.mean(req_scores)) if req_scores else 0.0
        score_gaps = [sc - threshold for sc in req_scores]
        score_gap_mean = float(np.mean(score_gaps)) if score_gaps else 0.0
        skills_below_threshold = sum(1 for g in score_gaps if g < 0)

        # ── nice-to-have feature ─────────────────────────────────────────────
        nice_scores = [s.get(skill, 0) for skill in nice if skill in s.index]
        nice_overlap = (
            sum(1 for sc in nice_scores if sc >= 50) / len(nice_scores)
            if nice_scores else 0.0
        )

        # ── student-level features ───────────────────────────────────────────
        all_scores = [s.get(skill, 0) for skill in ALL_SKILLS if skill in s.index]
        cgpa = float(s.get("cgpa", 0))
        cgpa_gap = cgpa - float(j["min_cgpa"])

        grad_year = int(s.get("graduation_year", 2024))
        recency = 2024 - grad_year  # 0 = just graduated

        feature_rows.append({
            "student_id": sid,
            "job_id": jid,
            "label": int(row["label"]),
            # ── core features ────────────────────────────────────────────────
            "skill_overlap_ratio": round(skill_overlap_ratio, 4),
            "mean_score_on_required": round(mean_score_on_required, 2),
            "score_gap_mean": round(score_gap_mean, 2),
            "skills_below_threshold": skills_below_threshold,
            "nice_to_have_overlap": round(nice_overlap, 4),
            "cgpa_gap": round(cgpa_gap, 2),
            "max_skill_score": float(max(all_scores)) if all_scores else 0.0,
            "avg_skill_score": round(float(np.mean(all_scores)), 2) if all_scores else 0.0,
            "graduation_recency": recency,
            "required_skills_count": len(required),
            "min_score_threshold": threshold,
        })

    return pd.DataFrame(feature_rows)


def split_and_save(features: pd.DataFrame):
    """
    Train / validation / test split — 60/20/20.
    Stratified on the label so each split has the same positive rate.
    """
    train_val, test = train_test_split(
        features, test_size=0.2, stratify=features["label"], random_state=42
    )
    train, val = train_test_split(
        train_val, test_size=0.25, stratify=train_val["label"], random_state=42
    )

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    train.to_csv(os.path.join(PROCESSED_DIR, "train.csv"), index=False)
    val.to_csv(os.path.join(PROCESSED_DIR, "val.csv"), index=False)
    test.to_csv(os.path.join(PROCESSED_DIR, "test.csv"), index=False)

    print(f"  Train : {len(train):>6,} rows  (positives: {train['label'].sum()})")
    print(f"  Val   : {len(val):>6,} rows  (positives: {val['label'].sum()})")
    print(f"  Test  : {len(test):>6,} rows  (positives: {test['label'].sum()})")

    return train, val, test


def main():
    print("Loading raw data...")
    students, jobs, labels = load_raw_data()
    print(f"  {len(students)} students, {len(jobs)} jobs, {len(labels)} pairs")

    print("\nBuilding features...")
    features = build_pair_features(students, jobs, labels)
    features.to_csv(os.path.join(PROCESSED_DIR, "features_all.csv"), index=False)
    print(f"  Feature matrix shape: {features.shape}")
    print(f"  Columns: {list(features.columns)}")
    print(f"  Label balance: {features['label'].value_counts().to_dict()}")

    print("\nSplitting into train/val/test...")
    split_and_save(features)

    print("\nDone. Features written to data/processed/")


if __name__ == "__main__":
    main()
