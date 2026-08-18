import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from src.features import engineer_features, get_feature_cols, TARGET_COL


def load_and_split(path: str):
    df = pd.read_csv(path)
    df = engineer_features(df)
    feature_cols = get_feature_cols(df)
    X = df[feature_cols]
    y = df[TARGET_COL]
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp)
    scaler = StandardScaler()
    X_train_s = pd.DataFrame(scaler.fit_transform(X_train), columns=feature_cols)
    X_val_s = pd.DataFrame(scaler.transform(X_val), columns=feature_cols)
    X_test_s = pd.DataFrame(scaler.transform(X_test), columns=feature_cols)
    return X_train_s, X_val_s, X_test_s, y_train, y_val, y_test, scaler, feature_cols
