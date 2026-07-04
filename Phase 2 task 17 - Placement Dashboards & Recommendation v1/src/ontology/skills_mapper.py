"""
Skills Mapper Module
Map student and job skills to ontology
"""

import json
from typing import Dict, List, Set


class SkillsMapper:
    """Map skills to standardized ontology."""
    
    def __init__(self, ontology_path: str = 'data/ontology/skills_ontology.json'):
        """Initialize with ontology file."""
        with open(ontology_path, 'r') as f:
            self.ontology = json.load(f)
        
        self.all_skills = self._build_skill_set()
        self.synonyms = self.ontology.get('synonyms', {})
    
    def _build_skill_set(self) -> Set[str]:
        """Build set of all known skills."""
        skills = set()
        for category in self.ontology.get('skills', {}).values():
            for skill_info in category:
                if isinstance(skill_info, dict):
                    skills.add(skill_info.get('name', ''))
                else:
                    skills.add(str(skill_info))
        return skills
    
    def normalize_skill(self, skill: str) -> str:
        """Normalize skill name (handle synonyms)."""
        if skill in self.synonyms:
            return self.synonyms[skill]
        return skill
    
    def is_known_skill(self, skill: str) -> bool:
        """Check if skill is in ontology."""
        normalized = self.normalize_skill(skill)
        return normalized in self.all_skills
    
    def map_skills(self, skills: List[str]) -> List[str]:
        """Map and normalize a list of skills."""
        mapped = []
        for skill in skills:
            normalized = self.normalize_skill(skill)
            if self.is_known_skill(skill):
                mapped.append(normalized)
        return mapped
    
    def get_related_skills(self, skill: str) -> List[str]:
        """Get skills related to a given skill."""
        relationships = self.ontology.get('skill_relationships', {})
        return relationships.get(skill, [])
    
    def get_skill_category(self, skill: str) -> str:
        """Get category of a skill."""
        for category, skills in self.ontology.get('skills', {}).items():
            for skill_info in skills:
                if isinstance(skill_info, dict) and skill_info.get('name') == skill:
                    return category
        return 'unknown'
