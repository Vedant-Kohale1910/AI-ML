import pandas as pd
import numpy as np

# Load dataset
df = pd.read_csv(r"C:\Users\vedan\PycharmProjects\AI-ML\Day 2 - Assesment difficulty prediction\data\student_assessment_dataset.csv")

print("Dataset Shape:", df.shape)

# Display first rows
print(df.head())

# Check missing values
print("\nMissing Values:\n")
print(df.isnull().sum())

# Fill numeric missing values
numeric_cols = df.select_dtypes(include=np.number).columns

for col in numeric_cols:
    df[col].fillna(df[col].median(), inplace=True)

# Fill categorical missing values
categorical_cols = df.select_dtypes(include='object').columns

for col in categorical_cols:
    df[col].fillna(df[col].mode()[0], inplace=True)

print("\nMissing values handled successfully!")

# Save cleaned dataset
df.to_csv(
    "cleaned_student_assessment_data.csv",
    index=False
)

print("\nCleaned dataset saved successfully!")