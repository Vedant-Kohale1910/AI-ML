import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from data_loader import load_data

#Creating student-level matrix
def build_matrix(df):
    matrix = df.pivot_table(index='student_id', columns='level_name', values='passed', fill_value=0)

    return matrix
#print(build_matrix(load_data()))

#Finding similar students
def find_similar_students(matrix, student_id):
    similarity =  cosine_similarity(matrix)
    similarity_df = pd.DataFrame(similarity, index=matrix.index, columns=matrix.index)
    similar_students = similarity_df[student_id].sort_values(ascending=False)

    return similar_students
#print(find_similar_students(build_matrix(load_data()), 1))

#Recommendation
def recommendation_levels(student_id, df):
    matrix = build_matrix(df)
    similar_students = find_similar_students(matrix, student_id)

    completed_levels = set(df[df["student_id"] == student_id]["level_name"])

    recommendations = {}
    for similar_student in similar_students.index:
        if similar_student == student_id:
            continue

        student_data = df[(df["student_id"] == similar_student) & (df["passed"] == 1)]

        for level in student_data["level_name"]:
            if level not in completed_levels:
                if level in recommendations:
                    recommendations[level] += 1
                else:
                    recommendations[level] = 1

    top_3_levels = sorted(recommendations.items(), key=lambda x: x[1], reverse=True)[:3]

    return top_3_levels
#print(recommendation_levels(1, load_data()))

if __name__ == "__main__":
    df = load_data()
    recommendations = recommendation_levels(97, df)
    print("Top Recommendations:\n")
    for level, score in recommendations:
        print(f"{level}: {score}")

