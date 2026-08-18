from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
import joblib


def train_baseline(X_train, y_train):
    """Task 9 tuned Random Forest as baseline."""
    param_grid = {'n_estimators': [100, 200], 'max_depth': [5, 10], 'min_samples_split': [5, 10]}
    rf = RandomForestClassifier(random_state=42)
    gs = GridSearchCV(rf, param_grid, cv=3, scoring='f1', n_jobs=-1)
    gs.fit(X_train, y_train)
    print(f"[Baseline] Best params: {gs.best_params_}")
    return gs.best_estimator_


def save_baseline(model, path):
    joblib.dump(model, path)
    print(f"[Baseline] Saved to {path}")


def load_baseline(path):
    return joblib.load(path)
