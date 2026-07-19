"""
Explainability Module
Generate plain-English explanations for recommendations
"""

from typing import Dict, List, Any


class ExplainabilityEngine:
    """Generate human-readable explanations for recommendations."""
    
    def explain_recommendation(self, student: Dict[str, Any], 
                             job: Dict[str, Any], 
                             features: Dict[str, Any],
                             score: float) -> Dict[str, Any]:
        """
        Generate detailed explanation for a recommendation.
        
        Args:
            student: Student profile
            job: Job profile
            features: Extracted features
            score: Final recommendation score
            
        Returns:
            Dictionary with explanation details
        """
        explanation = {
            'score': round(score * 100, 1),  # Convert to percentage
            'recommendation_level': self._get_recommendation_level(score),
            'skill_analysis': self._analyze_skills(student, job),
            'experience_analysis': self._analyze_experience(student, job),
            'assessment_analysis': self._analyze_assessment(student),
            'certification_analysis': self._analyze_certifications(student, job),
            'education_analysis': self._analyze_education(student, job),
            'summary': self._generate_summary(score, features, student, job)
        }
        
        return explanation
    
    def _get_recommendation_level(self, score: float) -> str:
        """Map score to recommendation level."""
        if score >= 0.85:
            return "STRONG MATCH"
        elif score >= 0.75:
            return "GOOD MATCH"
        elif score >= 0.60:
            return "FAIR MATCH"
        else:
            return "WEAK MATCH"
    
    def _analyze_skills(self, student: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze skill match in detail."""
        student_skills = set(student.get('verified_skills', []))
        required_skills = set(job.get('required_skills', []))
        nice_to_have = set(job.get('nice_to_have_skills', []))
        
        matched_required = student_skills & required_skills
        missing_required = required_skills - student_skills
        matched_nice = student_skills & nice_to_have
        missing_nice = nice_to_have - student_skills
        
        return {
            'required_skills': {
                'matched': list(matched_required),
                'missing': list(missing_required),
                'coverage': f"{len(matched_required)}/{len(required_skills)}"
            },
            'nice_to_have_skills': {
                'matched': list(matched_nice),
                'missing': list(missing_nice),
                'coverage': f"{len(matched_nice)}/{len(nice_to_have)}" if nice_to_have else "N/A"
            },
            'summary': f"{len(matched_required)} out of {len(required_skills)} required skills matched"
        }
    
    def _analyze_experience(self, student: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze experience match."""
        student_years = student.get('years_experience', 0)
        required_years = job.get('required_experience_years', 0)
        
        if student_years >= required_years:
            status = "✓ Exceeds requirement"
        elif student_years == required_years:
            status = "✓ Meets requirement"
        else:
            status = "✗ Below requirement"
        
        return {
            'student_years': student_years,
            'required_years': required_years,
            'status': status,
            'gap': max(0, required_years - student_years)
        }
    
    def _analyze_assessment(self, student: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze assessment score."""
        score = student.get('assessment_score', 0)
        
        if score >= 0.85:
            level = "Excellent"
        elif score >= 0.75:
            level = "Good"
        elif score >= 0.60:
            level = "Fair"
        else:
            level = "Below Average"
        
        return {
            'score': round(score, 2),
            'percentage': f"{round(score * 100, 1)}%",
            'level': level,
            'above_industry_benchmark': score >= 0.75
        }
    
    def _analyze_certifications(self, student: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze certification match."""
        student_certs = student.get('certifications', [])
        preferred_certs = job.get('preferred_certifications', [])
        
        matched = set(student_certs) & set(preferred_certs)
        
        return {
            'student_certifications': student_certs,
            'preferred_certifications': preferred_certs,
            'matched': list(matched),
            'has_preferred_cert': len(matched) > 0,
            'bonus': "Yes" if student_certs else "No"
        }
    
    def _analyze_education(self, student: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze education match."""
        student_edu = student.get('education', '')
        required_edu = job.get('education_requirement', '')
        
        return {
            'student_education': student_edu,
            'required_education': required_edu,
            'matches': self._check_education_match(student_edu, required_edu)
        }
    
    def _check_education_match(self, student_edu: str, required_edu: str) -> bool:
        """Check if student education meets requirement."""
        if not required_edu:
            return True
        
        student_lower = student_edu.lower()
        required_lower = required_edu.lower()
        
        # Simple matching logic
        if 'equivalent' in required_lower:
            return True
        
        # Check for degree level
        student_level = self._get_degree_level(student_lower)
        required_level = self._get_degree_level(required_lower)
        
        return student_level >= required_level
    
    def _get_degree_level(self, education: str) -> int:
        """Get education level (higher = more advanced)."""
        if 'master' in education or 'm.tech' in education or 'mba' in education:
            return 4
        elif 'b.tech' in education or 'bachelor' in education or 'btech' in education:
            return 3
        elif 'b.sc' in education or 'bsc' in education:
            return 2
        elif 'diploma' in education:
            return 1
        else:
            return 1  # Default
    
    def _generate_summary(self, score: float, features: Dict[str, Any], 
                        student: Dict[str, Any], job: Dict[str, Any]) -> str:
        """Generate executive summary."""
        recommendation_level = self._get_recommendation_level(score)
        
        skill_match = features.get('skill_match', 0)
        exp_match = features.get('experience_match', 0)
        assessment = student.get('assessment_score', 0)
        
        summary_parts = []
        
        if recommendation_level == "STRONG MATCH":
            summary_parts.append(f"Excellent fit for {job['title']}.")
            if skill_match >= 0.75:
                summary_parts.append("Strong skill alignment.")
            if exp_match >= 0.9:
                summary_parts.append("Experience requirement met or exceeded.")
            if assessment >= 0.85:
                summary_parts.append("Assessment score exceeds industry benchmark.")
        
        elif recommendation_level == "GOOD MATCH":
            summary_parts.append(f"Good candidate for {job['title']}.")
            summary_parts.append("Key skills present with strong potential.")
        
        elif recommendation_level == "FAIR MATCH":
            summary_parts.append(f"Potential fit for {job['title']}.")
            summary_parts.append("Core skills present but some development needed.")
        
        else:
            summary_parts.append(f"Limited match for {job['title']}.")
            summary_parts.append("Consider developing key skills first.")
        
        return " ".join(summary_parts)
    
    def format_explanation(self, explanation: Dict[str, Any]) -> str:
        """Format explanation as readable text."""
        text = f"""
RECOMMENDATION SCORE: {explanation['score']}% ({explanation['recommendation_level']})

SKILL ANALYSIS:
- Required Skills Matched: {explanation['skill_analysis']['required_skills']['coverage']}
  ✓ Matched: {', '.join(explanation['skill_analysis']['required_skills']['matched']) or 'None'}
  ✗ Missing: {', '.join(explanation['skill_analysis']['required_skills']['missing']) or 'None'}
- Nice-to-Have Skills: {', '.join(explanation['skill_analysis']['nice_to_have_skills']['matched']) or 'None'}

EXPERIENCE:
- Required: {explanation['experience_analysis']['required_years']} years
- Student Has: {explanation['experience_analysis']['student_years']} years
- Status: {explanation['experience_analysis']['status']}

ASSESSMENT SCORE:
- Score: {explanation['assessment_analysis']['percentage']}
- Level: {explanation['assessment_analysis']['level']}
- Above Benchmark: {explanation['assessment_analysis']['above_industry_benchmark']}

CERTIFICATIONS:
- Has Preferred Certs: {explanation['certification_analysis']['has_preferred_cert']}
- Bonus Applied: {explanation['certification_analysis']['bonus']}

SUMMARY:
{explanation['summary']}
        """
        return text.strip()
