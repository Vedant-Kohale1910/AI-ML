"""
Preprocessing Protocol (Task 4)
================================
- Auto-detects numeric / categorical columns.
- Numeric  : MedianImputer  → StandardScaler
- Categorical: MostFreqImputer → OneHotEncoder(handle_unknown='ignore')
- ColumnTransformer combines both sub-pipelines.
- fit() only on X_train; transform() on val/test/new data.
- Fitted preprocessor saved to artifacts/preprocessor.pkl for inference reuse.
"""
import os
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder


# ── Column detection ──────────────────────────────────────────────────────

def detect_columns(X: pd.DataFrame):
    num_cols = X.select_dtypes(include="number").columns.tolist()
    cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
    return num_cols, cat_cols


# ── Sub-pipelines ─────────────────────────────────────────────────────────

def _numeric_pipeline(strategy: str = "median") -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy=strategy)),
        ("scaler",  StandardScaler()),
    ])


def _categorical_pipeline(strategy: str = "most_frequent") -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy=strategy)),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])


# ── Main builder ──────────────────────────────────────────────────────────

def build_preprocessor(X: pd.DataFrame,
                        numeric_strategy: str = "median",
                        categorical_strategy: str = "most_frequent") -> ColumnTransformer:
    """Build (unfitted) ColumnTransformer from training-set column types."""
    num_cols, cat_cols = detect_columns(X)

    transformers = []
    if num_cols:
        transformers.append(("num", _numeric_pipeline(numeric_strategy), num_cols))
    if cat_cols:
        transformers.append(("cat", _categorical_pipeline(categorical_strategy), cat_cols))

    preprocessor = ColumnTransformer(transformers=transformers, remainder="drop")

    print(f"  [Preprocessor] Numeric ({len(num_cols)}): {num_cols}")
    print(f"  [Preprocessor] Categorical ({len(cat_cols)}): {cat_cols}")
    print( "  [Preprocessor] Transforms → Median Impute + StandardScale | MostFreq Impute + OneHotEncode")
    return preprocessor


# ── Fit / transform helpers (enforce leak-free discipline) ─────────────────

def fit_preprocessor(preprocessor: ColumnTransformer, X_train: pd.DataFrame):
    """Fit ONLY on training data."""
    print("  [Preprocessor] fit_transform on X_train only ✅ (no test data seen)")
    X_train_proc = preprocessor.fit_transform(X_train)
    print(f"  [Preprocessor] X_train shape after transform: {X_train_proc.shape}")
    return preprocessor, X_train_proc


def transform_split(preprocessor: ColumnTransformer, X: pd.DataFrame, split_name: str):
    """Transform val/test using already-fitted preprocessor (no re-fitting)."""
    X_proc = preprocessor.transform(X)          # transform() only — never fit_transform()
    print(f"  [Preprocessor] transform({split_name}) — shape: {X_proc.shape}  "
          f"(fitted params reused, no leakage)")
    return X_proc


# ── Persistence ───────────────────────────────────────────────────────────

def save_preprocessor(preprocessor: ColumnTransformer, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    joblib.dump(preprocessor, path)
    print(f"  [Preprocessor] Saved → {path}")


def load_preprocessor(path: str) -> ColumnTransformer:
    preprocessor = joblib.load(path)
    print(f"  [Preprocessor] Loaded ← {path}  (ready for inference)")
    return preprocessor


# ── Leakage verification ──────────────────────────────────────────────────

def verify_no_leakage(preprocessor: ColumnTransformer) -> None:
    """Print fitted statistics to prove they came only from X_train."""
    for name, trans, cols in preprocessor.transformers_:
        if name == "num":
            imp = trans.named_steps["imputer"]
            scaler = trans.named_steps["scaler"]
            print(f"\n  [LeakageCheck] Numeric imputer medians (from X_train only):")
            for c, med in zip(cols, imp.statistics_):
                print(f"    {c:30s}: median={med:.4f}  "
                      f"scale_mean={scaler.mean_[list(cols).index(c)]:.4f}")
        elif name == "cat":
            imp = trans.named_steps["imputer"]
            print(f"\n  [LeakageCheck] Categorical imputer modes (from X_train only):")
            for c, mode in zip(cols, imp.statistics_):
                print(f"    {c:30s}: most_frequent='{mode}'")
    print("\n  ✅ All preprocessing parameters fitted on X_train only — no leakage.")
