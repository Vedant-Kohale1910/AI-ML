"""
train_model.py

Builds the actual artifact that gets shipped: the TF-IDF matcher fitted on
the job pool, plus the alpha we tuned on the validation split in
evaluate.py. Bundled into one dict and dumped with joblib so the API layer
can load it without re-fitting anything at request time.

Run after evaluate.py (we need the tuned alpha):
    python src/train_model.py
"""

import joblib
import pandas as pd

from matching import TfidfMatcher
from evaluate import tune_alpha

MODEL_PATH = "../models/matching_model.pkl"


def build_and_save():
    jobs_df = pd.read_csv("../data/jobs.csv")
    students_df = pd.read_csv("../data/students.csv")
    val_df = students_df[students_df["split"] == "val"]

    matcher = TfidfMatcher(jobs_df)
    alpha, val_precision = tune_alpha(matcher, val_df)

    bundle = {
        "vectorizer": matcher.vectorizer,
        "job_matrix": matcher.job_matrix,
        "jobs_df": matcher.jobs_df,
        "job_skill_lists": matcher.job_skill_lists,
        "alpha": alpha,
        "top_n_default": 5,
        "trained_on": "synthetic v1, 80 jobs / 300 students",
    }

    joblib.dump(bundle, MODEL_PATH)
    print(f"saved model -> {MODEL_PATH} (alpha={alpha}, val precision@5={val_precision})")


if __name__ == "__main__":
    build_and_save()
