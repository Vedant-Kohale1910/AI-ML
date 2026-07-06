"""
Resume Parser Module
Converts raw resume text into structured student profile
"""

import json
from typing import Dict, List, Any


class ResumeParser:
    """Parse resume text and extract structured information."""
    
    def __init__(self):
        self.required_fields = [
            'name', 'email', 'verified_skills', 'years_experience',
            'education', 'assessment_score'
        ]
    
    def parse(self, resume_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse resume data into structured format.
        
        Args:
            resume_data: Dictionary containing resume information
            
        Returns:
            Structured student profile
        """
        parsed = {
            'student_id': resume_data.get('student_id'),
            'name': resume_data.get('name', ''),
            'email': resume_data.get('email', ''),
            'verified_skills': self._extract_skills(resume_data),
            'skill_levels': resume_data.get('skill_levels', {}),
            'years_experience': resume_data.get('years_experience', 0),
            'assessment_score': resume_data.get('assessment_score', 0.0),
            'education': resume_data.get('education', ''),
            'certifications': resume_data.get('certifications', []),
            'experience_summary': resume_data.get('experience_summary', ''),
        }
        
        # Validate
        self._validate(parsed)
        return parsed
    
    def _extract_skills(self, resume_data: Dict[str, Any]) -> List[str]:
        """Extract and deduplicate skills."""
        skills = resume_data.get('verified_skills', [])
        return list(set(skills))
    
    def _validate(self, parsed: Dict[str, Any]) -> None:
        """Validate parsed data."""
        if not parsed.get('verified_skills'):
            raise ValueError(f"Resume {parsed.get('student_id')}: No skills found")
        
        if not (0 <= parsed.get('assessment_score', 0) <= 1):
            raise ValueError(f"Resume {parsed.get('student_id')}: Invalid assessment score")
    
    def parse_batch(self, resumes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse multiple resumes."""
        parsed_resumes = []
        for resume in resumes:
            try:
                parsed = self.parse(resume)
                parsed_resumes.append(parsed)
            except ValueError as e:
                print(f"Warning: Skipping resume due to error: {e}")
        
        return parsed_resumes


def load_and_parse_students(json_path: str) -> List[Dict[str, Any]]:
    """Load and parse student data from JSON file."""
    with open(json_path, 'r') as f:
        students = json.load(f)
    
    parser = ResumeParser()
    return parser.parse_batch(students)
