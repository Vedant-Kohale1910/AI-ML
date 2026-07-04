"""
Job Description Parser Module
Converts raw job description into structured job profile
"""

import json
from typing import Dict, List, Any


class JDParser:
    """Parse job description and extract structured information."""
    
    def __init__(self):
        self.required_fields = [
            'title', 'company', 'required_skills', 'required_experience_years'
        ]
    
    def parse(self, jd_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse job description into structured format.
        
        Args:
            jd_data: Dictionary containing job information
            
        Returns:
            Structured job profile
        """
        parsed = {
            'job_id': jd_data.get('job_id'),
            'title': jd_data.get('title', ''),
            'company': jd_data.get('company', ''),
            'required_skills': self._extract_skills(jd_data.get('required_skills', [])),
            'nice_to_have_skills': self._extract_skills(jd_data.get('nice_to_have_skills', [])),
            'required_experience_years': jd_data.get('required_experience_years', 0),
            'education_requirement': jd_data.get('education_requirement', ''),
            'preferred_certifications': jd_data.get('preferred_certifications', []),
            'seniority_level': jd_data.get('seniority_level', 'mid'),
            'job_description': jd_data.get('job_description', ''),
        }
        
        # Validate
        self._validate(parsed)
        return parsed
    
    def _extract_skills(self, skills: List[str]) -> List[str]:
        """Extract and deduplicate skills."""
        return list(set(skills))
    
    def _validate(self, parsed: Dict[str, Any]) -> None:
        """Validate parsed data."""
        if not parsed.get('required_skills'):
            raise ValueError(f"Job {parsed.get('job_id')}: No required skills found")
        
        if parsed.get('required_experience_years', 0) < 0:
            raise ValueError(f"Job {parsed.get('job_id')}: Invalid experience requirement")
    
    def parse_batch(self, jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse multiple job descriptions."""
        parsed_jobs = []
        for job in jobs:
            try:
                parsed = self.parse(job)
                parsed_jobs.append(parsed)
            except ValueError as e:
                print(f"Warning: Skipping job due to error: {e}")
        
        return parsed_jobs


def load_and_parse_jobs(json_path: str) -> List[Dict[str, Any]]:
    """Load and parse job data from JSON file."""
    with open(json_path, 'r') as f:
        jobs = json.load(f)
    
    parser = JDParser()
    return parser.parse_batch(jobs)
