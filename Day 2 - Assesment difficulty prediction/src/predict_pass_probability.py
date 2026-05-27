import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Load Dataset
df = pd.read_csv("featured_student_assessment_data.csv")

# Features & Target
X = df.drop('passed', axis=1)
X = X.drop('student_id', axis=1)
y = df['passed']

# Train Test Split
X_train, X_test, y_train, y_test = train_test_split(X,y,test_size=0.2,random_state=42)

# Train Model
model = RandomForestClassifier(n_estimators=300, max_depth=10, random_state=42)
model.fit(X_train, y_train)

# Predict Probability
probabilities = model.predict_proba(X_test)
pass_probability = probabilities[:, 1]
prediction_df = pd.DataFrame({'Actual_Result': y_test.values, 'Pass_Probability': pass_probability})

print(prediction_df.head())