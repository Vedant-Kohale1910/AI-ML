"""
Feature Engineering Module
Extract and normalize features for recommendation scoring
"""

from typing import Dict, List, Any, Tuple
import json


class FeatureEngineer:
    """Extract and engineer features from student and job profiles."""
    
    def __init__(self):
        # Feature weights (sum to 1.0)
        self.feature_weights = {
            'skill_match': 0.50,
            'assessment_score': 0.20,
            'experience': 0.15,
            'certifications': 0.10,
            'education': 0.05
        }
    
    def extract_features(self, student: Dict[str, Any], job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features for a student-job pair.
        
        Args:
            student: Parsed student profile
            job: Parsed job profile
            
        Returns:
            Dictionary of extracted features
        """
        features = {
            'student_id': student.get('student_id'),
            'job_id': job.get('job_id'),
            'skill_match': self._compute_skill_match(student, job),
            'assessment_score': self._normalize_assessment(student.get('assessment_score', 0)),
            'experience_match': self._compute_experience_match(student, job),
            'certification_match': self._compute_certification_match(student, job),
            'education_level': self._map_education_level(student.get('education', '')),
        }
        
        return features
    
    def _compute_skill_match(self, student: Dict[str, Any], job: Dict[str, Any]) -> float:
        """
        Compute skill match score (0-1).
        
        Matched skills / Required skills + bonus for nice-to-have
        """
        student_skills = set(student.get('verified_skills', []))
        required_skills = set(job.get('required_skills', []))
        nice_to_have = set(job.get('nice_to_have_skills', []))
        
        if not required_skills:
            return 0.0
        
        # Core skill match
        matched_required = len(student_skills & required_skills)
        core_match = matched_required / len(required_skills)
        
        # Bonus for nice-to-have skills
        if nice_to_have:
            matched_nice = len(student_skills & nice_to_have)
            nice_bonus = (matched_nice / len(nice_to_have)) * 0.1
        else:
            nice_bonus = 0.0
        
        total_match = min(1.0, core_match + nice_bonus)
        return round(total_match, 3)
    
    def _compute_experience_match(self, student: Dict[str, Any], job: Dict[str, Any]) -> float:
        """
        Compute experience match (0-1).
        
        Binary: student has >= required experience
        """
        student_years = student.get('years_experience', 0)
        required_years = job.get('required_experience_years', 0)
        
        if student_years >= required_years:
            return 1.0
        else:
            # Partial credit: student has some experience
            if required_years == 0:
                return 1.0
            return round(student_years / required_years, 2)
    
    def _compute_certification_match(self, student: Dict[str, Any], job: Dict[str, Any]) -> float:
        """
        Compute certification bonus (0-0.1).
        
        Any relevant certification = 0.05 bonus
        """
        student_certs = set(student.get('certifications', []))
        required_certs = set(job.get('preferred_certifications', []))
        
        if not required_certs:
            # Bonus if student has any relevant certs
            if student_certs:
                return 0.05
            return 0.0
        
        # Match specific certs
        matched = len(student_certs & required_certs)
        if matched > 0:
            return 0.05
        return 0.0
    
    def _normalize_assessment(self, score: float) -> float:
        """Normalize assessment score (0-1)."""
        return min(1.0, max(0.0, score))
    
    def _map_education_level(self, education: str) -> float:
        """
        Map education to score (0-1).
        
        M.Tech / MBA: 1.0
        B.Tech: 0.8
        B.Sc: 0.7
        Diploma: 0.5
        """
        education_lower = education.lower()
        
        if 'm.tech' in education_lower or 'master' in education_lower or 'mba' in education_lower:
            return 1.0
        elif 'b.tech' in education_lower or 'btech' in education_lower or 'bachelor' in education_lower:
            return 0.8
        elif 'b.sc' in education_lower or 'bsc' in education_lower:
            return 0.7
        elif 'diploma' in education_lower:
            return 0.5
        else:
            return 0.6  # Default
    
    def compute_score(self, features: Dict[str, Any]) -> float:
        """
        Compute final recommendation score (0-1) using weighted features.
        
        Formula:
        Score = 0.50 × Skill Match
               + 0.20 × Assessment Score
               + 0.15 × Experience Match
               + 0.10 × Certification Match
               + 0.05 × Education Level
        """
        score = (
            self.feature_weights['skill_match'] * features.get('skill_match', 0) +
            self.feature_weights['assessment_score'] * features.get('assessment_score', 0) +
            self.feature_weights['experience'] * features.get('experience_match', 0) +
            self.feature_weights['certifications'] * features.get('certification_match', 0) +
            self.feature_weights['education'] * features.get('education_level', 0)
        )
        
        return round(min(1.0, max(0.0, score)), 3)
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance weights."""
        return self.feature_weights.copy()
