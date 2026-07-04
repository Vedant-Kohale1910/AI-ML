"""
Recommendation Engine v1 for PlaceMux
Matches students to jobs based on multiple weighted factors
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RecommendationScore:
    """Holds recommendation score and component breakdown"""
    job_id: int
    job_title: str
    overall_score: float
    skill_match_score: float
    assessment_score: float
    experience_match_score: float
    certification_score: float
    education_match_score: float
    explanation: str
    reasoning: Dict[str, str]


class RecommendationEngine:
    """
    Recommendation Engine v1 - Combines multiple signals to recommend jobs
    
    Scoring Formula:
    Overall Score = 0.50 × Skill Match 
                  + 0.20 × Assessment Score 
                  + 0.15 × Experience Match 
                  + 0.10 × Certification Match 
                  + 0.05 × Education Match
    """
    
    # Weights for recommendation formula
    WEIGHTS = {
        'skill_match': 0.50,
        'assessment_score': 0.20,
        'experience_match': 0.15,
        'certification': 0.10,
        'education': 0.05
    }
    
    def __init__(self, students_df: pd.DataFrame, jobs_df: pd.DataFrame):
        """
        Initialize recommendation engine with student and job data
        
        Args:
            students_df: DataFrame with student profiles
            jobs_df: DataFrame with job profiles
        """
        self.students = students_df.copy()
        self.jobs = jobs_df.copy()
        self._preprocess_data()
        
    def _preprocess_data(self):
        """Preprocess skill strings into lists"""
        self.students['skills_list'] = self.students['verified_skills'].apply(
            lambda x: [s.strip().lower() for s in str(x).split(',')]
        )
        self.jobs['required_skills_list'] = self.jobs['required_skills'].apply(
            lambda x: [s.strip().lower() for s in str(x).split(',')]
        )
    
    def _calculate_skill_match(self, student_skills: List[str], 
                              job_skills: List[str]) -> Tuple[float, List[str], List[str]]:
        """
        Calculate skill match score using Jaccard similarity
        
        Returns:
            (score, matched_skills, missing_skills)
        """
        student_skills_set = set(student_skills)
        job_skills_set = set(job_skills)
        
        matched = student_skills_set.intersection(job_skills_set)
        missing = job_skills_set - student_skills_set
        extra = student_skills_set - job_skills_set
        
        if len(job_skills_set) == 0:
            score = 1.0
        else:
            # Jaccard similarity: intersection / union
            score = len(matched) / len(job_skills_set)
        
        return score, list(matched), list(missing)
    
    def _calculate_experience_match(self, student_exp: float, 
                                   job_exp: float) -> Tuple[float, str]:
        """
        Calculate experience match
        
        Returns:
            (score, reason)
        """
        if student_exp >= job_exp:
            score = 1.0
            reason = f"Meets requirement ({student_exp:.1f}yrs >= {job_exp:.1f}yrs)"
        else:
            gap = job_exp - student_exp
            # Penalty for missing experience: -0.05 per missing year
            score = max(0.5, 1.0 - (gap * 0.05))
            reason = f"Below requirement by {gap:.1f} years ({student_exp:.1f}yrs < {job_exp:.1f}yrs)"
        
        return score, reason
    
    def _calculate_certification_match(self, student_certs: str, 
                                      job_preferred: str) -> Tuple[float, str]:
        """
        Calculate certification match
        
        Returns:
            (score, reason)
        """
        if pd.isna(job_preferred) or job_preferred == 'None' or job_preferred == '':
            score = 0.5  # Neutral score if no preference
            reason = "No specific certification preferred"
        else:
            job_certs = [c.strip().lower() for c in str(job_preferred).split(',')]
            student_cert_str = str(student_certs).lower()
            
            matched = sum(1 for cert in job_certs if cert in student_cert_str)
            score = matched / len(job_certs) if job_certs else 0.5
            
            if matched > 0:
                reason = f"Has {matched}/{len(job_certs)} preferred certifications"
            else:
                reason = f"Missing preferred certifications: {job_preferred}"
        
        return score, reason
    
    def _calculate_education_match(self, student_edu: str, 
                                  job_edu: str) -> Tuple[float, str]:
        """
        Calculate education level match
        
        Returns:
            (score, reason)
        """
        edu_hierarchy = {
            "high school": 1,
            "bachelor's": 2,
            "master's": 3,
            "phd": 4
        }
        
        student_level = next((edu_hierarchy.get(k, 0) for k in edu_hierarchy 
                             if k.lower() in student_edu.lower()), 0)
        job_level = next((edu_hierarchy.get(k, 0) for k in edu_hierarchy 
                         if k.lower() in job_edu.lower()), 0)
        
        if student_level >= job_level:
            score = 1.0
            reason = f"Meets education requirement ({student_edu})"
        else:
            score = 0.7
            reason = f"Below education requirement ({student_edu} < {job_edu})"
        
        return score, reason
    
    def _normalize_assessment_score(self, raw_score: float) -> float:
        """Normalize assessment score to 0-1 range (assuming 0-100 scale)"""
        return min(1.0, raw_score / 100.0)
    
    def recommend_jobs(self, student_id: int, top_n: int = 5) -> List[RecommendationScore]:
        """
        Generate top N job recommendations for a student
        
        Args:
            student_id: ID of student to recommend for
            top_n: Number of top recommendations to return
            
        Returns:
            List of RecommendationScore objects sorted by overall_score (highest first)
        """
        # Get student data
        student = self.students[self.students['student_id'] == student_id]
        if student.empty:
            logger.warning(f"Student {student_id} not found")
            return []
        
        student = student.iloc[0]
        recommendations = []
        
        # Score against each job
        for _, job in self.jobs.iterrows():
            # Calculate individual scores
            skill_score, matched, missing = self._calculate_skill_match(
                student['skills_list'],
                job['required_skills_list']
            )
            
            exp_score, exp_reason = self._calculate_experience_match(
                student['years_experience'],
                job['required_experience']
            )
            
            cert_score, cert_reason = self._calculate_certification_match(
                student['certifications'],
                job['preferred_certifications']
            )
            
            edu_score, edu_reason = self._calculate_education_match(
                student['education_level'],
                job['education_requirement']
            )
            
            assess_score = self._normalize_assessment_score(student['assessment_score'])
            
            # Calculate weighted overall score
            overall_score = (
                self.WEIGHTS['skill_match'] * skill_score +
                self.WEIGHTS['assessment_score'] * assess_score +
                self.WEIGHTS['experience_match'] * exp_score +
                self.WEIGHTS['certification'] * cert_score +
                self.WEIGHTS['education'] * edu_score
            )
            
            # Build explanation
            explanation_parts = []
            reasoning = {}
            
            if skill_score >= 0.8:
                explanation_parts.append(f"✓ Strong skill match ({len(matched)}/{len(job['required_skills_list'])} skills match)")
                reasoning['skills'] = f"Matched: {', '.join(matched)}"
            elif skill_score >= 0.5:
                explanation_parts.append(f"✓ Partial skill match ({len(matched)}/{len(job['required_skills_list'])} skills match)")
                reasoning['skills'] = f"Matched: {', '.join(matched)}. Missing: {', '.join(missing)}"
            else:
                explanation_parts.append(f"✗ Limited skill match ({len(matched)}/{len(job['required_skills_list'])} skills match)")
                reasoning['skills'] = f"Missing key skills: {', '.join(missing)}"
            
            if assess_score >= 0.85:
                explanation_parts.append(f"✓ Excellent assessment score ({student['assessment_score']}%)")
                reasoning['assessment'] = f"Score {student['assessment_score']}/100 is above average"
            elif assess_score >= 0.75:
                explanation_parts.append(f"✓ Good assessment score ({student['assessment_score']}%)")
                reasoning['assessment'] = f"Score {student['assessment_score']}/100 is competitive"
            else:
                explanation_parts.append(f"○ Assessment score: {student['assessment_score']}%")
                reasoning['assessment'] = f"Score {student['assessment_score']}/100 could be stronger"
            
            explanation_parts.append(f"→ {exp_reason}")
            reasoning['experience'] = exp_reason
            
            if cert_score >= 0.8:
                explanation_parts.append(f"✓ Has relevant certifications")
                reasoning['certifications'] = cert_reason
            else:
                explanation_parts.append(f"○ {cert_reason}")
                reasoning['certifications'] = cert_reason
            
            explanation_parts.append(f"→ {edu_reason}")
            reasoning['education'] = edu_reason
            
            explanation = " | ".join(explanation_parts)
            
            rec = RecommendationScore(
                job_id=job['job_id'],
                job_title=job['title'],
                overall_score=overall_score,
                skill_match_score=skill_score,
                assessment_score=assess_score,
                experience_match_score=exp_score,
                certification_score=cert_score,
                education_match_score=edu_score,
                explanation=explanation,
                reasoning=reasoning
            )
            
            recommendations.append(rec)
        
        # Sort by overall score (descending) and return top N
        recommendations.sort(key=lambda x: x.overall_score, reverse=True)
        return recommendations[:top_n]
    
    def get_recommendation_report(self, student_id: int, top_n: int = 5) -> Dict:
        """
        Generate a detailed recommendation report for a student
        
        Returns:
            Dictionary with student info, recommendations, and explanations
        """
        student = self.students[self.students['student_id'] == student_id].iloc[0]
        recommendations = self.recommend_jobs(student_id, top_n)
        
        return {
            'student_id': student_id,
            'student_name': student['name'],
            'student_profile': {
                'skills': student['verified_skills'],
                'experience_years': student['years_experience'],
                'assessment_score': student['assessment_score'],
                'certifications': student['certifications'],
                'education': student['education_level']
            },
            'top_recommendations': [
                {
                    'rank': i + 1,
                    'job_id': rec.job_id,
                    'job_title': rec.job_title,
                    'overall_score': round(rec.overall_score, 3),
                    'score_breakdown': {
                        'skill_match': round(rec.skill_match_score, 3),
                        'assessment': round(rec.assessment_score, 3),
                        'experience': round(rec.experience_match_score, 3),
                        'certification': round(rec.certification_score, 3),
                        'education': round(rec.education_match_score, 3)
                    },
                    'explanation': rec.explanation,
                    'reasoning': rec.reasoning
                }
                for i, rec in enumerate(recommendations)
            ],
            'scoring_weights': self.WEIGHTS
        }
