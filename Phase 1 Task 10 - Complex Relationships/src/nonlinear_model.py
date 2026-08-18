from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
import joblib


def train_nonlinear(X_train, y_train):
    """XGBoost with regularisation to control overfitting."""
    param_grid = {
        'n_estimators': [200, 300],
        'max_depth': [4, 6],
        'learning_rate': [0.05, 0.1],
        'subsample': [0.8],
        'colsample_bytree': [0.8],
        'reg_alpha': [0.1],
        'reg_lambda': [1.0],
        'min_child_weight': [3],
    }
    xgb = XGBClassifier(random_state=42, eval_metric='logloss', use_label_encoder=False)
    gs = GridSearchCV(xgb, param_grid, cv=3, scoring='f1', n_jobs=-1)
    gs.fit(X_train, y_train)
    print(f"[XGBoost] Best params: {gs.best_params_}")
    return gs.best_estimator_


def save_model(model, path):
    joblib.dump(model, path)
    print(f"[XGBoost] Saved to {path}")


def load_model(path):
    return joblib.load(path)
