def generate_explanation(student_profile: dict, job_recommendation: dict) -> str:
    """
    Ensures every recommendation includes a human-readable explanation.
    """
    matched = job_recommendation.get("skills_matched", [])
    missing = job_recommendation.get("skills_missing", [])
    
    explanation = ""
    for skill in matched:
        explanation += f"✓ {skill.capitalize()} matched\n"
        
    explanation += f"✓ Experience matched ({student_profile.get('experience_years', 0)} years)\n\n"
    
    if missing:
        explanation += "Missing:\n"
        for skill in missing:
            explanation += f"✗ {skill.capitalize()}\n"
            
    return explanation.strip()

def check_explainability(recommendations: list, student_profile: dict) -> bool:
    """
    Verifies that all recommendations can be explained.
    """
    for rec in recommendations:
        exp = generate_explanation(student_profile, rec)
        if not exp:
            return False
        rec["explanation"] = exp
    return True
