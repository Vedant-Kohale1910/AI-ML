"""Data loading and splitting — fits only on train split."""
import pandas as pd
from sklearn.model_selection import train_test_split


def load_data(path: str, drop_cols: list = None, target_col: str = "is_fraud"):
    df = pd.read_csv(path)
    if drop_cols:
        df = df.drop(columns=[c for c in drop_cols if c in df.columns])
    X = df.drop(columns=[target_col])
    y = df[target_col]
    print(f"  [Loader] {df.shape[0]} rows | {X.shape[1]} features | "
          f"missing cells: {X.isnull().sum().sum()} | "
          f"target balance: {y.value_counts().to_dict()}")
    return X, y


def split_data(X, y, val_size=0.15, test_size=0.15, random_seed=42):
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(
        X, y, test_size=val_size + test_size,
        random_state=random_seed, stratify=y)
    rel = test_size / (val_size + test_size)
    X_val, X_test, y_val, y_test = train_test_split(
        X_tmp, y_tmp, test_size=rel,
        random_state=random_seed, stratify=y_tmp)
    print(f"  [Loader] Train:{len(X_tr)} | Val:{len(X_val)} | Test:{len(X_test)}")
    return X_tr, X_val, X_test, y_tr, y_val, y_test
