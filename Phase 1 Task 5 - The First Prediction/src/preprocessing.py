"""Preprocessing — reused from Task 4 protocol."""
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import train_test_split


def load_and_split(path, target_col="is_fraud", val_size=0.15, test_size=0.15, seed=42):
    df = pd.read_csv(path)
    X = df.drop(columns=[target_col])
    y = df[target_col]
    X_tr, X_tmp, y_tr, y_tmp = train_test_split(X, y, test_size=val_size+test_size,
                                                  random_state=seed, stratify=y)
    rel = test_size / (val_size + test_size)
    X_val, X_test, y_val, y_test = train_test_split(X_tmp, y_tmp, test_size=rel,
                                                      random_state=seed, stratify=y_tmp)
    print(f"  Train:{len(X_tr)} Val:{len(X_val)} Test:{len(X_test)} | nulls:{X_tr.isnull().sum().sum()}")
    return X_tr, X_val, X_test, y_tr, y_val, y_test


def build_and_fit_preprocessor(X_train: pd.DataFrame):
    num_cols = X_train.select_dtypes(include="number").columns.tolist()
    cat_cols = X_train.select_dtypes(include="object").columns.tolist()
    num_pipe = Pipeline([("imp", SimpleImputer(strategy="median")),
                         ("scl", StandardScaler())])
    cat_pipe = Pipeline([("imp", SimpleImputer(strategy="most_frequent")),
                         ("enc", OneHotEncoder(handle_unknown="ignore", sparse_output=False))])
    ct = ColumnTransformer([("num", num_pipe, num_cols), ("cat", cat_pipe, cat_cols)])
    X_tr_proc = ct.fit_transform(X_train)          # fit ONLY on train
    return ct, X_tr_proc
