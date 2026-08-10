"""
data_loader.py — Load and verify the dataset.
"""

import pandas as pd
import numpy as np
import random

RANDOM_SEED = 42

def set_seeds(seed: int = RANDOM_SEED) -> None:
    random.seed(seed)
    np.random.seed(seed)

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df

def verify_data(df: pd.DataFrame, target_col: str = "default") -> dict:
    report = {
        "shape": df.shape,
        "dtypes": df.dtypes.to_dict(),
        "null_counts": df.isnull().sum().to_dict(),
        "duplicates": int(df.duplicated().sum()),
        "class_balance": df[target_col].value_counts().to_dict() if target_col in df.columns else None,
    }
    return report

if __name__ == "__main__":
    set_seeds()
    df = load_data("data/loan_default_dataset.csv")
    report = verify_data(df)
    print("Shape:", report["shape"])
    print("Nulls:", report["null_counts"])
    print("Duplicates:", report["duplicates"])
    print("Class balance:", report["class_balance"])
