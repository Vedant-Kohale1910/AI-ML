"""
Explainability Engine - Task 18
Generate clear, plain-English explanations for every recommendation
"""

from typing import Dict, List, Any, Tuple
import json


class ExplainabilityEngine:
    """Generate comprehensive explanations for job recommendations."""
    
    def __init__(self):
        """Initialize explainability engine."""
        self.recommendation_levels = {
            0.85: "STRONG MATCH",
            0.70: "GOOD MATCH",
            0.55: "FAIR MATCH",
            0.00: "WEAK MATCH"
        }
        
        self.recommendation_actions = {
            "STRONG MATCH": "Hire",
            "GOOD MATCH": "Consider",
            "FAIR MATCH": "Develop Skills",
            "WEAK MATCH": "Skip"
        }
    
    def generate_full_explanation(self, student: Dict[str, Any], 
                                 job: Dict[str, Any],
                                 features: Dict[str, Any],
                                 score: float) -> Dict[str, Any]:
        """
        Generate comprehensive explanation for a recommendation.
        
        Args:
            student: Student profile
            job: Job profile
            features: Extracted features
            score: Recommendation score (0-1)
            
        Returns:
            Complete explanation dictionary
        """
        recommendation_level = self._get_recommendation_level(score)
        
        explanation = {
            'recommendation_score': round(score, 3),
            'recommendation_percentage': round(score * 100, 1),
            'recommendation_level': recommendation_level,
            'recommendation_action': self.recommendation_actions.get(recommendation_level),
            
            'skill_analysis': self._analyze_skills(student, job),
            'assessment_analysis': self._analyze_assessment(student),
            'experience_analysis': self._analyze_experience(student, job),
            'certification_analysis': self._analyze_certifications(student, job),
            'education_analysis': self._analyze_education(student, job),
            
            'summary': self._generate_summary(score, student, job, features),
            'detailed_explanation': self._generate_detailed_explanation(
                score, student, job, features
            ),
            
            'strengths': self._identify_strengths(student, job),
            'gaps': self._identify_gaps(student, job),
            'confidence_level': self._get_confidence_level(score)
        }
        
        return explanation
    
    def _get_recommendation_level(self, score: float) -> str:
        """Get recommendation level based on score."""
        for threshold, level in sorted(self.recommendation_levels.items(), reverse=True):
            if score >= threshold:
                return level
        return "WEAK MATCH"
    
    def _analyze_skills(self, student: Dict[str, Any], 
                       job: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed skill analysis."""
        student_skills = set(student.get('verified_skills', []))
        required_skills = set(job.get('required_skills', []))
        nice_to_have = set(job.get('nice_to_have_skills', []))
        
        matched_required = student_skills & required_skills
        missing_required = required_skills - student_skills
        matched_nice = student_skills & nice_to_have
        missing_nice = nice_to_have - student_skills
        
        return {
            'required_skills': {
                'matched': sorted(list(matched_required)),
                'missing': sorted(list(missing_required)),
                'total_required': len(required_skills),
                'coverage': f"{len(matched_required)}/{len(required_skills)}",
                'coverage_percentage': round(100 * len(matched_required) / len(required_skills), 1) if required_skills else 0
            },
            'nice_to_have_skills': {
                'matched': sorted(list(matched_nice)),
                'missing': sorted(list(missing_nice)),
                'total': len(nice_to_have),
                'coverage': f"{len(matched_nice)}/{len(nice_to_have)}" if nice_to_have else "N/A",
                'coverage_percentage': round(100 * len(matched_nice) / len(nice_to_have), 1) if nice_to_have else 0
            },
            'summary': f"Strong skill match: {len(matched_required)}/{len(required_skills)} core requirements met" 
                      if len(matched_required) >= len(required_skills) * 0.7 
                      else f"Partial skill match: {len(matched_required)}/{len(required_skills)} core requirements met"
        }
    
    def _analyze_assessment(self, student: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze assessment score."""
        score = student.get('assessment_score', 0)
        benchmark = 0.75  # Industry benchmark
        
        return {
            'student_score': round(score, 2),
            'student_percentage': round(score * 100, 1),
            'industry_benchmark': round(benchmark, 2),
            'benchmark_percentage': round(benchmark * 100, 1),
            'difference': round(score - benchmark, 2),
            'difference_percentage': round((score - benchmark) * 100, 1),
            'status': 'Above benchmark' if score >= benchmark else 'Below benchmark',
            'level': self._get_assessment_level(score),
            'summary': f"Assessment score {round(score * 100, 1)}% {'exceeds' if score >= benchmark else 'is below'} " + 
                      f"industry benchmark of {round(benchmark * 100, 1)}%"
        }
    
    def _get_assessment_level(self, score: float) -> str:
        """Get assessment level description."""
        if score >= 0.85:
            return "Excellent"
        elif score >= 0.75:
            return "Good"
        elif score >= 0.60:
            return "Fair"
        else:
            return "Below Average"
    
    def _analyze_experience(self, student: Dict[str, Any], 
                           job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze experience match."""
        student_years = student.get('years_experience', 0)
        required_years = job.get('required_experience_years', 0)
        
        gap = required_years - student_years if student_years < required_years else 0
        
        if student_years > required_years:
            status = "Exceeds requirement"
            exceeds_by = student_years - required_years
        elif student_years == required_years:
            status = "Meets requirement exactly"
            exceeds_by = 0
        else:
            status = "Below requirement"
            exceeds_by = 0
        
        return {
            'required_years': required_years,
            'student_years': student_years,
            'gap': gap,
            'exceeds_by': exceeds_by,
            'status': status,
            'summary': f"Experience: {student_years} years " + 
                      f"({'meets' if student_years >= required_years else 'needs ' + str(gap) + ' more'} " +
                      f"requirement of {required_years} years)"
        }
    
    def _analyze_certifications(self, student: Dict[str, Any], 
                               job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze certifications."""
        student_certs = set(student.get('certifications', []))
        preferred_certs = set(job.get('preferred_certifications', []))
        
        matched = student_certs & preferred_certs
        
        return {
            'student_certifications': sorted(list(student_certs)),
            'preferred_certifications': sorted(list(preferred_certs)),
            'matched_certifications': sorted(list(matched)),
            'has_preferred': len(matched) > 0,
            'count': len(student_certs),
            'summary': f"Has {len(student_certs)} certifications" +
                      (f"; {len(matched)} match job preference" if len(matched) > 0 else "")
        }
    
    def _analyze_education(self, student: Dict[str, Any], 
                          job: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze education match."""
        student_edu = student.get('education', '')
        required_edu = job.get('education_requirement', '')
        
        student_level = self._get_education_level(student_edu)
        required_level = self._get_education_level(required_edu)
        
        matches = student_level >= required_level
        
        return {
            'student_education': student_edu,
            'required_education': required_edu,
            'student_level': student_level,
            'required_level': required_level,
            'matches': matches,
            'summary': f"Education: {student_edu} " +
                      ("meets requirement" if matches else "below requirement")
        }
    
    def _get_education_level(self, education: str) -> int:
        """Get education level ranking."""
        education_lower = education.lower()
        
        if 'master' in education_lower or 'm.tech' in education_lower or 'mba' in education_lower:
            return 4
        elif 'b.tech' in education_lower or 'bachelor' in education_lower or 'btech' in education_lower:
            return 3
        elif 'b.sc' in education_lower or 'bsc' in education_lower:
            return 2
        elif 'diploma' in education_lower:
            return 1
        else:
            return 1
    
    def _identify_strengths(self, student: Dict[str, Any], 
                           job: Dict[str, Any]) -> List[str]:
        """Identify candidate strengths."""
        strengths = []
        
        student_skills = set(student.get('verified_skills', []))
        required_skills = set(job.get('required_skills', []))
        
        # Skill coverage
        if len(student_skills & required_skills) == len(required_skills):
            strengths.append("All core required skills present")
        
        # Assessment
        if student.get('assessment_score', 0) >= 0.85:
            strengths.append("Assessment score well above industry benchmark")
        elif student.get('assessment_score', 0) >= 0.75:
            strengths.append("Assessment score meets or exceeds benchmark")
        
        # Experience
        if student.get('years_experience', 0) > job.get('required_experience_years', 0):
            strengths.append("Exceeds required experience")
        
        # Certifications
        if student.get('certifications', []):
            strengths.append(f"Has {len(student.get('certifications', []))} relevant certifications")
        
        # Education
        if self._get_education_level(student.get('education', '')) >= \
           self._get_education_level(job.get('education_requirement', '')):
            strengths.append("Education aligns with requirements")
        
        return strengths
    
    def _identify_gaps(self, student: Dict[str, Any], 
                      job: Dict[str, Any]) -> List[str]:
        """Identify candidate gaps."""
        gaps = []
        
        student_skills = set(student.get('verified_skills', []))
        missing_skills = set(job.get('required_skills', [])) - student_skills
        
        # Missing skills
        if missing_skills:
            for skill in sorted(missing_skills):
                gaps.append(f"Missing skill: {skill}")
        
        # Experience gap
        exp_gap = job.get('required_experience_years', 0) - student.get('years_experience', 0)
        if exp_gap > 0:
            gaps.append(f"Experience gap: {exp_gap} year(s) below requirement")
        
        # Assessment
        if student.get('assessment_score', 0) < 0.75:
            gaps.append(f"Assessment score below benchmark")
        
        return gaps
    
    def _get_confidence_level(self, score: float) -> Dict[str, Any]:
        """Get confidence level and explanation."""
        if score >= 0.85:
            level = "Very High"
            percentage = 95
        elif score >= 0.75:
            level = "High"
            percentage = 85
        elif score >= 0.60:
            level = "Moderate"
            percentage = 70
        else:
            level = "Low"
            percentage = 50
        
        return {
            'level': level,
            'percentage': percentage,
            'description': f"Confidence in this match is {level.lower()}"
        }
    
    def _generate_summary(self, score: float, student: Dict[str, Any], 
                         job: Dict[str, Any], features: Dict[str, Any]) -> str:
        """Generate executive summary."""
        level = self._get_recommendation_level(score)
        student_name = student.get('name', 'Candidate')
        job_title = job.get('title', 'Position')
        
        if level == "STRONG MATCH":
            return f"{student_name} is an excellent match for {job_title}. " + \
                   "Core requirements are met with strong alignment across skills, " + \
                   "assessment score, and experience."
        
        elif level == "GOOD MATCH":
            return f"{student_name} is a good fit for {job_title}. " + \
                   "Key skills are present with adequate experience and assessment performance."
        
        elif level == "FAIR MATCH":
            return f"{student_name} could be a fit for {job_title}. " + \
                   "Core skills are partially present; some development needed."
        
        else:
            return f"{student_name} is not a strong fit for {job_title}. " + \
                   "Multiple skill gaps and/or insufficient experience."
    
    def _generate_detailed_explanation(self, score: float, student: Dict[str, Any],
                                      job: Dict[str, Any], 
                                      features: Dict[str, Any]) -> str:
        """Generate detailed plain-English explanation."""
        parts = []
        
        level = self._get_recommendation_level(score)
        job_title = job.get('title', 'Position')
        
        # Start with recommendation
        parts.append(f"Recommended for {job_title} with confidence score of {round(score*100, 1)}%")
        parts.append(f"Recommendation Level: {level}")
        
        # Skills
        skill_analysis = self._analyze_skills(student, job)
        if skill_analysis['required_skills']['coverage_percentage'] == 100:
            parts.append(f"✓ All {skill_analysis['required_skills']['total_required']} required skills present")
        else:
            coverage = skill_analysis['required_skills']['coverage_percentage']
            parts.append(f"✓ {coverage}% of required skills present ({skill_analysis['required_skills']['coverage']})")
        
        # Missing skills
        missing = skill_analysis['required_skills']['missing']
        if missing:
            parts.append(f"✗ Missing skills: {', '.join(missing)}")
        
        # Assessment
        assess = self._analyze_assessment(student)
        if assess['status'] == 'Above benchmark':
            parts.append(f"✓ Assessment score {assess['student_percentage']}% exceeds benchmark ({assess['benchmark_percentage']}%)")
        else:
            parts.append(f"Assessment score {assess['student_percentage']}% is below benchmark ({assess['benchmark_percentage']}%)")
        
        # Experience
        exp = self._analyze_experience(student, job)
        if exp['gap'] == 0:
            parts.append(f"✓ Experience requirement met: {exp['student_years']} years (required {exp['required_years']})")
        else:
            parts.append(f"✗ Experience gap: {exp['student_years']} years vs {exp['required_years']} required")
        
        # Final recommendation
        action = self.recommendation_actions.get(level, 'Consider')
        parts.append(f"RECOMMENDATION: {action}")
        
        return " | ".join(parts)
    
    def to_formatted_text(self, explanation: Dict[str, Any]) -> str:
        """Format explanation as readable text."""
        text = f"""
RECOMMENDATION ANALYSIS
{'='*70}

RECOMMENDATION SCORE: {explanation['recommendation_percentage']}%
LEVEL: {explanation['recommendation_level']}
ACTION: {explanation['recommendation_action']}

SKILL ANALYSIS:
{self._format_skill_analysis(explanation['skill_analysis'])}

ASSESSMENT SCORE:
{self._format_assessment_analysis(explanation['assessment_analysis'])}

EXPERIENCE:
{self._format_experience_analysis(explanation['experience_analysis'])}

CERTIFICATIONS:
{self._format_certification_analysis(explanation['certification_analysis'])}

EDUCATION:
{self._format_education_analysis(explanation['education_analysis'])}

STRENGTHS:
{chr(10).join('✓ ' + s for s in explanation['strengths'])}

GAPS:
{chr(10).join('✗ ' + g for g in explanation['gaps']) if explanation['gaps'] else 'None identified'}

SUMMARY:
{explanation['summary']}

CONFIDENCE: {explanation['confidence_level']['level']} ({explanation['confidence_level']['percentage']}%)
        """
        return text.strip()
    
    def _format_skill_analysis(self, skill_analysis: Dict[str, Any]) -> str:
        req = skill_analysis['required_skills']
        return f"""
  Required Skills: {req['coverage']} ({req['coverage_percentage']}%)
  Matched: {', '.join(req['matched']) if req['matched'] else 'None'}
  Missing: {', '.join(req['missing']) if req['missing'] else 'None'}
  Summary: {skill_analysis['summary']}
        """
    
    def _format_assessment_analysis(self, assess: Dict[str, Any]) -> str:
        return f"""
  Student Score: {assess['student_percentage']}%
  Benchmark: {assess['benchmark_percentage']}%
  Difference: {assess['difference_percentage']:+.1f}%
  Status: {assess['status']}
  Summary: {assess['summary']}
        """
    
    def _format_experience_analysis(self, exp: Dict[str, Any]) -> str:
        return f"""
  Required: {exp['required_years']} years
  Student Has: {exp['student_years']} years
  Gap: {exp['gap']} year(s)
  Status: {exp['status']}
  Summary: {exp['summary']}
        """
    
    def _format_certification_analysis(self, cert: Dict[str, Any]) -> str:
        return f"""
  Student Certs: {cert['count']}
  Has Preferred: {'Yes' if cert['has_preferred'] else 'No'}
  Summary: {cert['summary']}
        """
    
    def _format_education_analysis(self, edu: Dict[str, Any]) -> str:
        return f"""
  Student: {edu['student_education']}
  Required: {edu['required_education']}
  Matches: {'Yes' if edu['matches'] else 'No'}
  Summary: {edu['summary']}
        """
