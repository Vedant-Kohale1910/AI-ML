import pandas as pd
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report


# Load Dataset
df = pd.read_csv("cleaned_student_assessment_data.csv")

# Features & Target
X = df.drop('passed', axis=1)

# Remove ID column
X = X.drop('student_id', axis=1)

y = df['passed']

# Train Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

# Scaling
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Cross Validation Setup
skf = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

# Logistic Regression
log_model = LogisticRegression(max_iter=2000, random_state=42)

log_scores = cross_validate(
    log_model,
    X_train_scaled,
    y_train,
    cv=skf,
    scoring=[
        'accuracy',
        'precision',
        'recall',
        'f1'
    ]
)

print("\nLogistic Regression")
print("Accuracy:", log_scores['test_accuracy'].mean())
("Precision:", log_scores['test_precision'].mean())
print("Recall:", log_scores['test_recall'].mean())
print("F1 Score:", log_scores['test_f1'].mean())

# Random Forest
rf_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=10,
    random_state=42
)

rf_scores = cross_validate(
    rf_model,
    X_train,
    y_train,
    cv=skf,
    scoring=[
        'accuracy',
        'precision',
        'recall',
        'f1'
    ]
)

print("\n Random Forest")
print("Accuracy:", rf_scores['test_accuracy'].mean())
print("Precision:", rf_scores['test_precision'].mean())
print("Recall:", rf_scores['test_recall'].mean())
print("F1 Score:", rf_scores['test_f1'].mean())

# XGBoost
xgb_model = XGBClassifier(
    n_estimators=300,
    learning_rate=0.05,
    max_depth=6,
    eval_metric='logloss',
    random_state=42
)

xgb_scores = cross_validate(
    xgb_model,
    X_train,
    y_train,
    cv=skf,
    scoring=[
        'accuracy',
        'precision',
        'recall',
        'f1'
    ]
)

print("\nXGBoost")
print("Accuracy:", xgb_scores['test_accuracy'].mean())
print("Precision:", xgb_scores['test_precision'].mean())
print("Recall:", xgb_scores['test_recall'].mean())
print("F1 Score:", xgb_scores['test_f1'].mean())


# Final Random Forest Training
rf_model.fit(X_train, y_train)

rf_preds = rf_model.predict(X_test)

print("\nFinal Test Results\n")
print(classification_report(y_test,rf_preds))