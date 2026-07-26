"""
Learning-to-Rank (LTR) Model — Stage B
========================================
Approach chosen: LightGBM with LambdaRank (listwise/pairwise objective).

Why LambdaMART/GBDT over a neural ranker?
  * Interpretable feature importances — required for "explain why Job A > Job B".
  * Trains on small interaction logs (50 students) without over-fitting.
  * Directly optimises nDCG (LambdaRank gradient), not a proxy loss.
  * Fast to train, easy to version and audit (model-versioning pitfall avoided).

Why rejected: Neural cross-encoder ranker (BERT-style) needs far more data
and GPU resources; over-kill for this interaction volume.

Label hierarchy (what is closest to real business value?):
  shortlist=3 > apply=2 > click (debiased)=1 > impression only=0
"""
import json
import numpy as np
import pandas as pd
import lightgbm as lgb
import joblib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.retrieval.feature_engineering import FeatureEngineer
from src.ranking.bias_correction import debias_labels

MODEL_VERSION = "ltr-v1.0"
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../reports/ltr_model.pkl")


def build_feature_matrix(students: list, jobs: list, interactions: pd.DataFrame):
    """
    Build (X, y, qid, rank) arrays for LambdaRank training.
    One row = one (student, job) pair that was impressed.
    Features reuse the Phase-2 FeatureEngineer — no train/serve skew.
    """
    fe = FeatureEngineer()
    student_map = {s["student_id"]: s for s in students}
    job_map = {j["job_id"]: j for j in jobs}

    rows, labels, qids, ranks = [], [], [], []
    imps = interactions[interactions["event_type"] == "impression"].copy()

    # Build outcome labels per (student, job, session)
    clicks = set(zip(
        interactions[interactions["event_type"] == "click"]["student_id"],
        interactions[interactions["event_type"] == "click"]["job_id"],
        interactions[interactions["event_type"] == "click"]["session_id"],
    ))
    applies = set(zip(
        interactions[interactions["event_type"] == "apply"]["student_id"],
        interactions[interactions["event_type"] == "apply"]["job_id"],
        interactions[interactions["event_type"] == "apply"]["session_id"],
    ))
    shortlists = set(zip(
        interactions[interactions["event_type"] == "shortlist"]["student_id"],
        interactions[interactions["event_type"] == "shortlist"]["job_id"],
        interactions[interactions["event_type"] == "shortlist"]["session_id"],
    ))

    for _, row in imps.iterrows():
        sid, jid, sess = int(row["student_id"]), int(row["job_id"]), row["session_id"]
        rank_pos = int(row["rank_position"])
        student = student_map.get(sid)
        job = job_map.get(jid)
        if not student or not job:
            continue

        feats = fe.extract_features(student, job)
        feat_vec = [
            feats.get("skill_match", 0),
            feats.get("assessment_score", 0),
            feats.get("experience_match", 0),
            feats.get("certification_match", 0),
            float(row["score"]),
        ]

        # Label: shortlist=3, apply=2, debiased click=1, else=0
        key = (sid, jid, sess)
        if key in shortlists:
            label = 3.0
        elif key in applies:
            label = 2.0
        elif key in clicks:
            # apply IPS debiasing for click label
            debiased = debias_labels(
                np.array([rank_pos]), np.array([1.0])
            )[0]
            label = min(1.0, debiased)   # clip to max 1.0 for the label tier
        else:
            label = 0.0

        rows.append(feat_vec)
        labels.append(label)
        qids.append(sid)
        ranks.append(rank_pos)

    X = np.array(rows, dtype=np.float32)
    y = np.array(labels, dtype=np.float32)
    return X, y, np.array(qids), np.array(ranks)


FEATURE_NAMES = [
    "skill_match", "assessment_score", "experience_match",
    "certification_match", "retrieval_score",
]


def train(X, y, qids):
    """Train LightGBM LambdaRank model."""
    # Group sizes (items per query) required by LambdaRank
    _, counts = np.unique(qids, return_counts=True)
    groups = counts.tolist()

    train_data = lgb.Dataset(X, label=y, group=groups,
                              feature_name=FEATURE_NAMES)
    params = {
        "objective": "lambdarank",
        "metric": "ndcg",
        "ndcg_eval_at": [5, 10],
        "learning_rate": 0.05,
        "num_leaves": 15,
        "min_data_in_leaf": 1,
        "verbose": -1,
        "seed": 42,
    }
    model = lgb.train(params, train_data, num_boost_round=80)
    return model


def predict_scores(model, X):
    return model.predict(X)


def save_model(model, path=MODEL_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump({"model": model, "version": MODEL_VERSION,
                 "feature_names": FEATURE_NAMES}, path)


def load_model(path=MODEL_PATH):
    return joblib.load(path)
