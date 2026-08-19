from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier

RANDOM_STATE = 42


def get_base_models():
    return {
        'Logistic Regression': LogisticRegression(max_iter=1000, random_state=RANDOM_STATE, C=0.5),
        'Random Forest': RandomForestClassifier(n_estimators=200, max_depth=8,
                                                min_samples_split=10, random_state=RANDOM_STATE),
        'XGBoost': XGBClassifier(n_estimators=200, max_depth=4, learning_rate=0.05,
                                  subsample=0.8, colsample_bytree=0.8, reg_alpha=0.1,
                                  reg_lambda=1.0, random_state=RANDOM_STATE,
                                  eval_metric='logloss', use_label_encoder=False),
    }
