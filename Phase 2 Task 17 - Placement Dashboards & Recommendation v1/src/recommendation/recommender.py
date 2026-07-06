"""
Recommendation Engine Module
Core recommendation logic
"""

import json
from typing import Dict, List, Any
from .feature_engineering import FeatureEngineer


class RecommendationEngine:
    """Generate recommendations for students based on job matching."""
    
    def __init__(self, min_score_threshold: float = 0.5):
        """
        Initialize recommendation engine.
        
        Args:
            min_score_threshold: Minimum score to recommend a job (0-1)
        """
        self.feature_engineer = FeatureEngineer()
        self.min_score_threshold = min_score_threshold
        self.students = {}
        self.jobs = {}
    
    def load_students(self, students: List[Dict[str, Any]]) -> None:
        """Load student profiles."""
        for student in students:
            self.students[student['student_id']] = student
    
    def load_jobs(self, jobs: List[Dict[str, Any]]) -> None:
        """Load job profiles."""
        for job in jobs:
            self.jobs[job['job_id']] = job
    
    def recommend(self, student_id: int, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Generate top-k job recommendations for a student.
        
        Args:
            student_id: Student ID
            top_k: Number of recommendations to return
            
        Returns:
            List of recommended jobs with scores
        """
        if student_id not in self.students:
            raise ValueError(f"Student {student_id} not found")
        
        student = self.students[student_id]
        scores = []
        
        # Score student against all jobs
        for job_id, job in self.jobs.items():
            features = self.feature_engineer.extract_features(student, job)
            score = self.feature_engineer.compute_score(features)
            
            # Only include if above threshold
            if score >= self.min_score_threshold:
                scores.append({
                    'job_id': job_id,
                    'title': job['title'],
                    'company': job['company'],
                    'score': score,
                    'features': features
                })
        
        # Sort by score (descending) and return top-k
        scores.sort(key=lambda x: x['score'], reverse=True)
        return scores[:top_k]
    
    def recommend_with_details(self, student_id: int, top_k: int = 5) -> Dict[str, Any]:
        """
        Generate recommendations with feature details.
        
        Args:
            student_id: Student ID
            top_k: Number of recommendations
            
        Returns:
            Dictionary with student info and recommendations
        """
        student = self.students.get(student_id)
        if not student:
            raise ValueError(f"Student {student_id} not found")
        
        recommendations = self.recommend(student_id, top_k)
        
        return {
            'student_id': student_id,
            'student_name': student.get('name'),
            'student_skills': student.get('verified_skills', []),
            'recommended_jobs': recommendations,
            'total_jobs_evaluated': len(self.jobs),
            'jobs_above_threshold': len([r for r in 
                self.recommend(student_id, len(self.jobs))])
        }
    
    def batch_recommend(self, student_ids: List[int], top_k: int = 5) -> Dict[int, List[Dict[str, Any]]]:
        """
        Generate recommendations for multiple students.
        
        Args:
            student_ids: List of student IDs
            top_k: Number of recommendations per student
            
        Returns:
            Dictionary mapping student_id to recommendations
        """
        results = {}
        for student_id in student_ids:
            try:
                results[student_id] = self.recommend(student_id, top_k)
            except ValueError as e:
                print(f"Warning: {e}")
        
        return results
    
    def get_baseline_score(self, student_id: int, job_id: int) -> float:
        """
        Compute baseline score (skill overlap only).
        
        Baseline = (matched_skills / required_skills) × 100
        """
        student = self.students.get(student_id)
        job = self.jobs.get(job_id)
        
        if not student or not job:
            return 0.0
        
        student_skills = set(student.get('verified_skills', []))
        required_skills = set(job.get('required_skills', []))
        
        if not required_skills:
            return 0.0
        
        matched = len(student_skills & required_skills)
        return round((matched / len(required_skills)), 3)
