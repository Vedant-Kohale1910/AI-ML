"""Fairness Metrics Calculator - Task 21"""
from typing import Dict, List, Any

class FairnessMetrics:
    @staticmethod
    def calculate_disparate_impact(selection_rates: Dict[str, float]) -> Dict[str, Any]:
        """Calculate disparate impact ratio."""
        if len(selection_rates) < 2:
            return {}
        rates = list(selection_rates.values())
        max_rate = max(rates)
        min_rate = min(rates)
        return {
            'disparate_impact': min_rate / max_rate if max_rate > 0 else 0,
            'status': 'FAIR' if min_rate / max_rate >= 0.80 else 'BIASED'
        }
    
    @staticmethod
    def calculate_equal_opportunity(groups: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Calculate equal opportunity metric."""
        results = {}
        for group, data in groups.items():
            qualified = data.get('qualified', 0)
            recommended = data.get('recommended', 0)
            results[group] = recommended / qualified if qualified > 0 else 0
        return results
    
    @staticmethod
    def calculate_calibration(groups: Dict[str, Dict[str, int]]) -> Dict[str, Any]:
        """Calculate calibration metric."""
        results = {}
        for group, data in groups.items():
            recommended = data.get('recommended', 0)
            qualified_recommended = data.get('qualified_recommended', 0)
            results[group] = qualified_recommended / recommended if recommended > 0 else 0
        return results
