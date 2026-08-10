"""
train.py — Split data, run smoke-test model, log metrics.
"""

import csv
import os
import random
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import train_test_split

RANDOM_SEED = 42


def set_seeds(seed: int = RANDOM_SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)


def split_data(df: pd.DataFrame, target_col: str = "default",
               val_size: float = 0.15, test_size: float = 0.15):
    X = df.drop(columns=[target_col])
    y = df[target_col]

    # First split: train vs temp (val+test)
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=(val_size + test_size), random_state=RANDOM_SEED, stratify=y
    )

    # Second split: val vs test from temp
    rel_test = test_size / (val_size + test_size)
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=rel_test, random_state=RANDOM_SEED, stratify=y_temp
    )

    print(f"Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    return X_train, X_val, X_test, y_train, y_val, y_test


def run_smoke_test(X_train, X_val, y_train, y_val):
    clf = DummyClassifier(strategy="most_frequent", random_state=RANDOM_SEED)
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_val)
    acc = round(accuracy_score(y_val, y_pred), 4)
    f1 = round(f1_score(y_val, y_pred, zero_division=0), 4)
    return clf, acc, f1


def log_metrics(model_name: str, accuracy: float, f1: float,
                dataset: str, params: str, log_path: str = "metrics.csv") -> None:
    file_exists = os.path.isfile(log_path)
    with open(log_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "model", "accuracy", "f1_score", "dataset", "params"])
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model": model_name,
            "accuracy": accuracy,
            "f1_score": f1,
            "dataset": dataset,
            "params": params,
        })
    print(f"Logged → {log_path}: {model_name} | acc={accuracy} | f1={f1}")


if __name__ == "__main__":
    set_seeds()
    df = pd.read_csv("data/loan_default_dataset.csv")
    X_train, X_val, X_test, y_train, y_val, y_test = split_data(df)
    clf, acc, f1 = run_smoke_test(X_train, X_val, y_train, y_val)
    log_metrics("DummyClassifier", acc, f1, "loan_default_dataset.csv", "strategy=most_frequent")
    print(f"Smoke test PASSED — Val Accuracy: {acc}, Val F1: {f1}")
