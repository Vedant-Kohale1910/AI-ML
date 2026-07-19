"""
Feature Importance Module - Task 18
Calculate and explain feature contributions to recommendation score
"""

from typing import Dict, List, Any, Tuple


class FeatureImportanceCalculator:
    """Calculate and explain feature contributions."""
    
    def __init__(self):
        """Initialize with feature weights."""
        self.feature_weights = {
            'skill_match': 0.50,
            'assessment_score': 0.20,
            'experience': 0.15,
            'certifications': 0.10,
            'education': 0.05
        }
    
    def calculate_contributions(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate each feature's contribution to final score.
        
        Args:
            features: Extracted features dictionary
            
        Returns:
            Dictionary with contribution breakdown
        """
        contributions = {}
        total_contribution = 0.0
        
        for feature_name, weight in self.feature_weights.items():
            value = features.get(feature_name, 0)
            contribution = round(value * weight, 4)
            
            contributions[feature_name] = {
                'value': round(value, 3),
                'weight': weight,
                'weight_percentage': round(weight * 100, 1),
                'contribution': contribution,
                'contribution_to_final': round(contribution * 100, 1),
                'description': self._get_feature_description(feature_name, value)
            }
            
            total_contribution += contribution
        
        contributions['total_score'] = round(total_contribution, 3)
        contributions['total_percentage'] = round(total_contribution * 100, 1)
        
        return contributions
    
    def get_feature_breakdown_table(self, contributions: Dict[str, Any]) -> str:
        """
        Format feature contributions as a table.
        
        Returns ASCII table with contributions
        """
        table = """
┌────────────────────┬────────┬────────┬──────────────┐
│ Feature            │ Value  │ Weight │ Contribution │
├────────────────────┼────────┼────────┼──────────────┤
"""
        
        for feature_name in ['skill_match', 'assessment_score', 'experience', 
                            'certifications', 'education']:
            if feature_name in contributions:
                feature = contributions[feature_name]
                table += f"│ {feature_name:<18} │ {feature['value']:>6.2f} │ {feature['weight_percentage']:>5.1f}% │ {feature['contribution']:>11.3f}  │\n"
        
        table += "├────────────────────┼────────┼────────┼──────────────┤\n"
        table += f"│ TOTAL              │        │ 100.0% │ {contributions['total_score']:>11.3f}  │\n"
        table += """└────────────────────┴────────┴────────┴──────────────┘
        """
        return table
    
    def _get_feature_description(self, feature_name: str, value: float) -> str:
        """Get human-readable description of feature value."""
        if feature_name == 'skill_match':
            if value >= 0.90:
                return "Strong skill match: most/all required skills present"
            elif value >= 0.70:
                return "Good skill match: majority of required skills present"
            elif value >= 0.50:
                return "Fair skill match: some required skills present"
            else:
                return "Weak skill match: few required skills present"
        
        elif feature_name == 'assessment_score':
            if value >= 0.85:
                return "Excellent: well above industry benchmark"
            elif value >= 0.75:
                return "Good: meets or exceeds industry benchmark"
            elif value >= 0.60:
                return "Fair: below benchmark but acceptable"
            else:
                return "Poor: significantly below benchmark"
        
        elif feature_name == 'experience':
            if value >= 1.0:
                return "Exceeds requirement: has equal or more years than required"
            elif value >= 0.75:
                return "Near requirement: close to required years"
            elif value >= 0.5:
                return "Below requirement: some experience but gaps remain"
            else:
                return "Insufficient: significantly below required experience"
        
        elif feature_name == 'certifications':
            if value >= 0.5:
                return "Has relevant certifications"
            else:
                return "No or few relevant certifications"
        
        elif feature_name == 'education':
            if value >= 0.8:
                return "Strong educational background"
            elif value >= 0.6:
                return "Adequate education level"
            else:
                return "Below expected education level"
        
        return "Feature present"
    
    def rank_features_by_contribution(self, contributions: Dict[str, Any]) -> List[Tuple[str, float]]:
        """
        Rank features by their contribution to score.
        
        Returns:
            List of (feature_name, contribution) tuples sorted by contribution
        """
        feature_contributions = []
        
        for feature_name in ['skill_match', 'assessment_score', 'experience',
                            'certifications', 'education']:
            if feature_name in contributions:
                feature_contributions.append(
                    (feature_name, contributions[feature_name]['contribution'])
                )
        
        return sorted(feature_contributions, key=lambda x: x[1], reverse=True)
    
    def get_most_impactful_features(self, contributions: Dict[str, Any], 
                                   top_n: int = 3) -> List[str]:
        """Get top N most impactful features."""
        ranked = self.rank_features_by_contribution(contributions)
        return [feature for feature, _ in ranked[:top_n]]
    
    def get_improvement_opportunities(self, features: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify which features could be improved.
        
        Returns:
            List of improvement opportunities
        """
        opportunities = []
        
        # Check each feature
        if features.get('skill_match', 0) < 0.90:
            gap = round(0.90 - features.get('skill_match', 0), 2)
            opportunities.append({
                'feature': 'skill_match',
                'current': round(features.get('skill_match', 0), 2),
                'target': 0.90,
                'gap': gap,
                'potential_gain': round(gap * self.feature_weights['skill_match'], 3),
                'action': 'Learn missing skills or find jobs matching current skills'
            })
        
        if features.get('assessment_score', 0) < 0.85:
            gap = round(0.85 - features.get('assessment_score', 0), 2)
            opportunities.append({
                'feature': 'assessment_score',
                'current': round(features.get('assessment_score', 0), 2),
                'target': 0.85,
                'gap': gap,
                'potential_gain': round(gap * self.feature_weights['assessment_score'], 3),
                'action': 'Improve skills to boost assessment score'
            })
        
        if features.get('experience', 0) < 1.0:
            gap = round(1.0 - features.get('experience', 0), 2)
            opportunities.append({
                'feature': 'experience',
                'current': round(features.get('experience', 0), 2),
                'target': 1.0,
                'gap': gap,
                'potential_gain': round(gap * self.feature_weights['experience'], 3),
                'action': 'Gain more relevant work experience'
            })
        
        if features.get('certifications', 0) < 0.5:
            opportunities.append({
                'feature': 'certifications',
                'current': round(features.get('certifications', 0), 2),
                'target': 0.5,
                'gap': round(0.5 - features.get('certifications', 0), 2),
                'potential_gain': round(0.05, 3),
                'action': 'Earn relevant professional certifications'
            })
        
        # Sort by potential gain
        opportunities.sort(key=lambda x: x['potential_gain'], reverse=True)
        
        return opportunities
    
    def get_improvement_roadmap(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an improvement roadmap for the candidate.
        
        Returns:
            Structured roadmap with priorities and actions
        """
        opportunities = self.get_improvement_opportunities(features)
        
        roadmap = {
            'current_score': round(sum(
                features.get(f, 0) * self.feature_weights[f]
                for f in self.feature_weights.keys()
            ), 3),
            'opportunities': opportunities,
            'potential_score_with_improvements': round(sum(
                features.get(f, 0) * self.feature_weights[f]
                for f in self.feature_weights.keys()
            ) + sum(opp['potential_gain'] for opp in opportunities), 3),
            'total_potential_gain': round(sum(opp['potential_gain'] for opp in opportunities), 3),
            'priority_actions': [opp['action'] for opp in opportunities[:3]],
            'estimated_improvement_timeline': self._estimate_timeline(opportunities)
        }
        
        return roadmap
    
    def _estimate_timeline(self, opportunities: List[Dict[str, Any]]) -> str:
        """Estimate timeline for improvements."""
        if not opportunities:
            return "No improvements needed"
        
        num_improvements = len(opportunities)
        
        if num_improvements == 1:
            return "3-6 months for the primary improvement"
        elif num_improvements == 2:
            return "6-12 months for all improvements"
        else:
            return "12-18 months for comprehensive improvement"
    
    def generate_improvement_summary(self, features: Dict[str, Any]) -> str:
        """
        Generate a readable improvement summary.
        
        Returns:
            Plain-text summary of improvements
        """
        roadmap = self.get_improvement_roadmap(features)
        
        text = f"""
IMPROVEMENT ROADMAP
{'='*60}

Current Score: {roadmap['current_score']:.1%}
Potential Score with Improvements: {roadmap['potential_score_with_improvements']:.1%}
Potential Gain: {roadmap['total_potential_gain']:.1%}

PRIORITY ACTIONS:
"""
        
        for i, action in enumerate(roadmap['priority_actions'], 1):
            text += f"{i}. {action}\n"
        
        text += f"\nEstimated Timeline: {roadmap['estimated_improvement_timeline']}\n"
        
        return text.strip()
    
    def get_feature_comparison(self, current_features: Dict[str, Any],
                              benchmark_features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare current features to benchmark.
        
        Returns:
            Comparison dictionary
        """
        comparison = {}
        
        for feature_name in self.feature_weights.keys():
            current = current_features.get(feature_name, 0)
            benchmark = benchmark_features.get(feature_name, 0)
            
            comparison[feature_name] = {
                'current': round(current, 3),
                'benchmark': round(benchmark, 3),
                'difference': round(current - benchmark, 3),
                'difference_percentage': round((current - benchmark) * 100, 1),
                'status': 'Above benchmark' if current > benchmark else 
                         ('Meets benchmark' if current == benchmark else 'Below benchmark'),
                'gap_to_close': round(max(0, benchmark - current), 3)
            }
        
        return comparison
