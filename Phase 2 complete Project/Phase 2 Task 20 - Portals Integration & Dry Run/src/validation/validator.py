# Mocks the recommendation v1 engine output for testing
def run_recommendation_v1(student_profile: dict, jobs: list) -> list:
    """
    Simulates Recommendation Engine v1 running on a test dataset.
    Returns a list of recommended jobs with scores.
    """
    recommendations = []
    student_skills = [s.lower() for s in student_profile.get("skills", [])]
    
    for job in jobs:
        job_skills = [s.lower() for s in job.get("skills", [])]
        overlap = len(set(student_skills).intersection(set(job_skills)))
        
        # Recommendation v1 is slightly smarter, assigns extra weight to experience
        # This is just a mock for the validation module
        score = min(100, (overlap / max(1, len(job_skills))) * 100 + (student_profile.get("experience_years", 0) * 5))
        
        if score > 60: # threshold
            recommendations.append({
                "job_id": job.get("job_id"),
                "job_title": job.get("title"),
                "score": round(score, 2),
                "skills_matched": list(set(student_skills).intersection(set(job_skills))),
                "skills_missing": list(set(job_skills) - set(student_skills))
            })
            
    return sorted(recommendations, key=lambda x: x["score"], reverse=True)
