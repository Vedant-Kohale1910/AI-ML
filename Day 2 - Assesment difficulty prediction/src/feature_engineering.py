import pandas as pd
from sklearn.preprocessing import OneHotEncoder

# Load cleaned dataset
df = pd.read_csv(r"C:\Users\vedan\PycharmProjects\AI-ML\Day 2 - Assesment difficulty prediction\src\student_assessment_dataset.csv")

# One Hot Encoding
encoder = OneHotEncoder(sparse_output=False)
encoded = encoder.fit_transform(df[['question_difficulty']])

encoded_df = pd.DataFrame(encoded, columns=encoder.get_feature_names_out(['question_difficulty']))

df = pd.concat([df.reset_index(drop=True), encoded_df.reset_index(drop=True)], axis=1)

df.drop('question_difficulty', axis=1, inplace=True)

# Study Related Features
study_cols = [
    'study_hours_per_week',
    'hours_studied_for_assessment',
    'study_sessions_last_30_days'
]

df['total_study_effort'] = (df[study_cols].sum(axis=1))
df['avg_study_effort'] = (df[study_cols].mean(axis=1))
df['study_consistency'] = (df[study_cols].std(axis=1))

# Score Related Features
score_cols = ['previous_scores', 'avg_previous_score']

df['ability_score'] = (df[score_cols].mean(axis=1))
df['score_consistency'] = (df[score_cols].std(axis=1))

# Advanced Features
df['preparedness_score'] = (df['ability_score'] * 0.6 + df['avg_study_effort'] * 0.4)

df['study_efficiency'] = (df['ability_score'] / (df['avg_study_effort'] + 1))

df['performance_index'] = (df['engagement_score'] + df['ability_score']) / 2

# Save feature engineered dataset
df.to_csv("cleaned_student_assessment_data.csv", index=False)

print("Success!")