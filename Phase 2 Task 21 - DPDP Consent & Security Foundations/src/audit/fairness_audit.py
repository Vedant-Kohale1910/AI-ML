"""Fairness Audit Engine - Task 21"""
from typing import Dict, List, Any

class FairnessAudit:
    def audit_by_group(self, recommendations: List[Dict[str, Any]], 
                      group_field: str) -> Dict[str, Any]:
        """Audit recommendations by demographic group."""
        groups = {}
        for rec in recommendations:
            group_value = rec.get(group_field, 'Unknown')
            if group_value not in groups:
                groups[group_value] = []
            groups[group_value].append(rec)
        
        results = {'group_field': group_field, 'groups': {}}
        for group_name, group_recs in groups.items():
            total = len(group_recs)
            recommended = sum(1 for r in group_recs if r.get('recommended', False))
            results['groups'][group_name] = {
                'total': total,
                'recommended': recommended,
                'recommendation_rate': recommended / total if total > 0 else 0,
                'avg_score': sum(r.get('score', 0) for r in group_recs) / total if total > 0 else 0
            }
        
        results['disparities'] = self._calculate_disparities(results['groups'])
        return results
    
    def _calculate_disparities(self, groups: Dict) -> Dict[str, Any]:
        """Calculate disparities between groups."""
        if len(groups) < 2:
            return {}
        rates = {g: v['recommendation_rate'] for g, v in groups.items()}
        max_rate = max(rates.values())
        min_rate = min(rates.values())
        return {
            'max_rate': max_rate,
            'min_rate': min_rate,
            'disparity_percentage': (max_rate - min_rate) * 100,
            'disparate_impact': min_rate / max_rate if max_rate > 0 else 0
        }
    
    def detect_bias(self, disparate_impact: float) -> Dict[str, Any]:
        """Detect if bias exists."""
        if disparate_impact < 0.60:
            bias_level = "SEVERE"
            confidence = 0.95
        elif disparate_impact < 0.80:
            bias_level = "MODERATE"
            confidence = 0.85
        elif disparate_impact < 0.95:
            bias_level = "MILD"
            confidence = 0.70
        else:
            bias_level = "NO_BIAS"
            confidence = 0.5
        
        return {
            'bias_level': bias_level,
            'disparate_impact': disparate_impact,
            'confidence': confidence,
            'requires_action': bias_level != "NO_BIAS"
        }
