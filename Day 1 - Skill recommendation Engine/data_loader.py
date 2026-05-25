import pandas as pd

def load_data():
    df = pd.read_csv(r"C:\Users\vedan\PycharmProjects\AI-ML\Day 1 - Skill recommendation Engine\student_progress.csv")
    return df

#print(load_data())