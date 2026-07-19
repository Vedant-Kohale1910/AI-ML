def calculate_baseline_score(student_skills: list, job_skills: list) -> float:
    """
    Calculate a simple skill-overlap recommender score.
    Returns percentage of job skills met by the student.
    """
    if not job_skills:
        return 0.0
    
    student_skills_set = set([s.lower() for s in student_skills])
    job_skills_set = set([s.lower() for s in job_skills])
    
    overlap = student_skills_set.intersection(job_skills_set)
    return round((len(overlap) / len(job_skills_set)) * 100, 2)
