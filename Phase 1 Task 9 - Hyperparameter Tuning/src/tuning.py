"""
Hyperparameter tuning module — Task 9.
Uses RandomizedSearchCV with 5-fold CV on the training set ONLY.
Test set is never touched during tuning.
"""
import json, os
import numpy as np
import pandas as pd
from sklearn.model_selection import RandomizedSearchCV, StratifiedKFold, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score

# ── Parameter space for Random Forest ────────────────────────────────────
# Only tuning parameters that meaningfully affect bias/variance trade-off
PARAM_DISTRIBUTIONS = {
    "model__n_estimators":    [100, 200, 300, 500],
    "model__max_depth":       [None, 10, 15, 20, 30],
    "model__min_samples_split":[2, 5, 10],
    "model__min_samples_leaf": [1, 2, 4],
    "model__max_features":    ["sqrt", "log2"],
}

# Baseline config from Task 8
BASELINE_CONFIG = {
    "n_estimators": 100,
    "class_weight": "balanced",
    "random_state": 42
}

BASELINE_TEST_METRICS = {
    "f1_macro": 0.6961,
    "accuracy": 0.7067,
    "roc_auc": 0.7917
}


def run_random_search(pipeline, X_train, y_train,
                      n_iter=30, cv_folds=5, seed=42) -> RandomizedSearchCV:
    """Run RandomizedSearchCV on training data only."""
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    search = RandomizedSearchCV(
        estimator=pipeline,
        param_distributions=PARAM_DISTRIBUTIONS,
        n_iter=n_iter,
        scoring="f1_macro",
        cv=cv,
        random_state=seed,
        n_jobs=-1,
        refit=True,          # refit best params on full training set
        verbose=1,
        return_train_score=False,
    )
    print(f"  [Tuning] RandomizedSearchCV: {n_iter} iterations × {cv_folds}-fold CV")
    print(f"  [Tuning] Scoring: f1_macro | Seed: {seed}")
    print(f"  [Tuning] Parameters being tuned: {list(PARAM_DISTRIBUTIONS.keys())}")
    search.fit(X_train, y_train)
    return search


def extract_cv_results(search: RandomizedSearchCV) -> pd.DataFrame:
    """Extract all CV results into a sorted DataFrame."""
    df = pd.DataFrame(search.cv_results_)
    keep = [c for c in df.columns if c.startswith(("param_", "mean_test", "std_test", "rank_test"))]
    df = df[keep].sort_values("rank_test_score").reset_index(drop=True)
    df.columns = [c.replace("param_model__","").replace("mean_test_score","mean_cv_f1")
                   .replace("std_test_score","std_cv_f1").replace("rank_test_score","rank") for c in df.columns]
    return df


def save_tuning_artifacts(search, comparison_df: pd.DataFrame,
                           out_dir="artifacts") -> dict:
    os.makedirs(out_dir, exist_ok=True)
    best = search.best_params_
    best_cv = round(search.best_score_, 4)

    result = {
        "best_parameters": {k.replace("model__", ""): v for k, v in best.items()},
        "best_cv_f1_macro": best_cv,
        "cv_folds": 5,
        "n_iterations": 30,
        "baseline_test_f1": BASELINE_TEST_METRICS["f1_macro"],
    }

    path = os.path.join(out_dir, "tuning_results.json")
    with open(path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"  [Artifacts] tuning_results.json → {path}")
    return result
