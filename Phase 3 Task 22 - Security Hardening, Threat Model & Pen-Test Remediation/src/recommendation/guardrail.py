"""
Guardrail Module
Quality checks and validation for recommendations
"""

from typing import Dict, List, Any, Tuple


class GuardrailValidator:
    """Validate recommendations for quality and safety."""
    
    def __init__(self):
        self.min_skill_overlap = 0.3  # Minimum 30% skill overlap
        self.min_score = 0.5
        self.max_experience_gap = 2  # Max 2 years below requirement
    
    def validate_recommendation(self, student: Dict[str, Any], 
                               job: Dict[str, Any],
                               score: float) -> Tuple[bool, str]:
        """
        Validate a single recommendation.
        
        Args:
            student: Student profile
            job: Job profile
            score: Recommendation score
            
        Returns:
            (is_valid, reason) tuple
        """
        checks = [
            self._check_minimum_score(score),
            self._check_skill_overlap(student, job),
            self._check_experience_gap(student, job),
            self._check_data_quality(student, job)
        ]
        
        for is_valid, reason in checks:
            if not is_valid:
                return False, reason
        
        return True, "Recommendation passed all checks"
    
    def _check_minimum_score(self, score: float) -> Tuple[bool, str]:
        """Check if score meets minimum threshold."""
        if score >= self.min_score:
            return True, "Score above minimum threshold"
        return False, f"Score {score:.2f} below minimum {self.min_score}"
    
    def _check_skill_overlap(self, student: Dict[str, Any], 
                            job: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if skill overlap is sufficient."""
        student_skills = set(student.get('verified_skills', []))
        required_skills = set(job.get('required_skills', []))
        
        if not required_skills:
            return True, "No skill requirements"
        
        overlap = len(student_skills & required_skills) / len(required_skills)
        
        if overlap >= self.min_skill_overlap:
            return True, f"Sufficient skill overlap: {overlap:.1%}"
        
        return False, f"Insufficient skill overlap: {overlap:.1%} < {self.min_skill_overlap:.1%}"
    
    def _check_experience_gap(self, student: Dict[str, Any], 
                             job: Dict[str, Any]) -> Tuple[bool, str]:
        """Check experience gap doesn't exceed threshold."""
        student_years = student.get('years_experience', 0)
        required_years = job.get('required_experience_years', 0)
        gap = max(0, required_years - student_years)
        
        if gap <= self.max_experience_gap:
            return True, f"Experience gap acceptable: {gap} years"
        
        return False, f"Experience gap too large: {gap} > {self.max_experience_gap}"
    
    def _check_data_quality(self, student: Dict[str, Any], 
                           job: Dict[str, Any]) -> Tuple[bool, str]:
        """Check data quality of profiles."""
        # Check student data
        if not student.get('verified_skills'):
            return False, "Student has no verified skills"
        
        if not isinstance(student.get('assessment_score'), (int, float)):
            return False, "Invalid assessment score"
        
        # Check job data
        if not job.get('required_skills'):
            return False, "Job has no required skills"
        
        if not isinstance(job.get('required_experience_years'), (int, float)):
            return False, "Invalid experience requirement"
        
        return True, "Data quality check passed"
    
    def validate_batch(self, students: List[Dict[str, Any]], 
                      jobs: List[Dict[str, Any]],
                      scores: Dict[Tuple[int, int], float]) -> Dict[str, Any]:
        """
        Validate batch of recommendations.
        
        Returns summary of validation results
        """
        valid_count = 0
        invalid_count = 0
        issues = []
        
        for (student_id, job_id), score in scores.items():
            student = next((s for s in students if s['student_id'] == student_id), None)
            job = next((j for j in jobs if j['job_id'] == job_id), None)
            
            if not student or not job:
                continue
            
            is_valid, reason = self.validate_recommendation(student, job, score)
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                issues.append({
                    'student_id': student_id,
                    'job_id': job_id,
                    'reason': reason
                })
        
        return {
            'total': valid_count + invalid_count,
            'valid': valid_count,
            'invalid': invalid_count,
            'validity_rate': f"{100 * valid_count / (valid_count + invalid_count):.1f}%" if (valid_count + invalid_count) > 0 else "N/A",
            'issues': issues[:10]  # Show first 10 issues
        }
    
    def get_quality_report(self, students: List[Dict[str, Any]], 
                          jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate data quality report."""
        return {
            'students': {
                'count': len(students),
                'with_skills': sum(1 for s in students if s.get('verified_skills')),
                'with_assessment': sum(1 for s in students if s.get('assessment_score')),
                'avg_skills': sum(len(s.get('verified_skills', [])) for s in students) / len(students) if students else 0
            },
            'jobs': {
                'count': len(jobs),
                'with_requirements': sum(1 for j in jobs if j.get('required_skills')),
                'avg_required_skills': sum(len(j.get('required_skills', [])) for j in jobs) / len(jobs) if jobs else 0
            }
        }
