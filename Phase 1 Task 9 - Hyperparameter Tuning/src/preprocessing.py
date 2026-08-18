"""Preprocessing inside sklearn Pipeline — preprocessing travels WITH the model."""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split
from src.features import FEATURE_COLS, TARGET_COL


def split_data(df: pd.DataFrame, val_size=0.15, test_size=0.15, seed=42):
    X = df[[c for c in FEATURE_COLS if c in df.columns]]
    y = df[TARGET_COL]
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(
        X, y, test_size=val_size+test_size, random_state=seed, stratify=y)
    rel = test_size / (val_size + test_size)
    X_val, X_test, y_val, y_test = train_test_split(
        X_tmp, y_tmp, test_size=rel, random_state=seed, stratify=y_tmp)
    return X_tr, X_val, X_test, y_tr, y_val, y_test


def build_full_pipeline(X_train: pd.DataFrame, model) -> Pipeline:
    """Chain ColumnTransformer + model into ONE sklearn Pipeline (pipeline integrity)."""
    num_cols = X_train.select_dtypes(include="number").columns.tolist()
    cat_cols = X_train.select_dtypes(include="object").columns.tolist()
    steps = []
    if num_cols:
        steps.append(("num", Pipeline([
            ("imp", SimpleImputer(strategy="median")),
            ("scl", StandardScaler())]), num_cols))
    if cat_cols:
        steps.append(("cat", Pipeline([
            ("imp", SimpleImputer(strategy="most_frequent")),
            ("enc", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]), cat_cols))
    preprocessor = ColumnTransformer(steps)
    return Pipeline([("preprocessor", preprocessor), ("model", model)])
