"""Feature preprocessing using sklearn Pipeline."""
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
import pandas as pd


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    """Auto-detect numeric and categorical columns, return ColumnTransformer."""
    num_cols = X.select_dtypes(include="number").columns.tolist()
    cat_cols = X.select_dtypes(include="object").columns.tolist()

    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    steps = []
    if num_cols:
        steps.append(("num", num_pipeline, num_cols))
    if cat_cols:
        steps.append(("cat", cat_pipeline, cat_cols))

    preprocessor = ColumnTransformer(transformers=steps)
    print(f"  [Preprocessor] Numeric: {num_cols} | Categorical: {cat_cols}")
    return preprocessor
