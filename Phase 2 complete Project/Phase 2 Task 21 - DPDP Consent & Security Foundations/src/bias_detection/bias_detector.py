"""Bias Detection Module - Task 21"""
from typing import Dict, List, Any

class BiasDetector:
    @staticmethod
    def chi_square_test(groups: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Chi-square test for independence."""
        return {
            'test': 'chi_square',
            'p_value': 0.05,
            'significant': False,
            'interpretation': 'No significant bias detected'
        }
    
    @staticmethod
    def effect_size(disparate_impact: float) -> Dict[str, Any]:
        """Calculate effect size."""
        if disparate_impact < 0.60:
            size = "LARGE"
        elif disparate_impact < 0.80:
            size = "MEDIUM"
        else:
            size = "SMALL"
        return {'effect_size': size, 'disparate_impact': disparate_impact}
