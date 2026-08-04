"""
Ranking Module
Rank and order recommendations
"""

from typing import List, Dict, Any


class RankingEngine:
    """Rank and sort job recommendations."""
    
    def rank_recommendations(self, recommendations: List[Dict[str, Any]], 
                            method: str = 'score') -> List[Dict[str, Any]]:
        """
        Rank recommendations using specified method.
        
        Args:
            recommendations: List of recommendation dictionaries
            method: Ranking method ('score', 'weighted', 'percentile')
            
        Returns:
            Ranked list of recommendations
        """
        if method == 'score':
            return self._rank_by_score(recommendations)
        elif method == 'weighted':
            return self._rank_by_weighted_score(recommendations)
        elif method == 'percentile':
            return self._rank_by_percentile(recommendations)
        else:
            raise ValueError(f"Unknown ranking method: {method}")
    
    def _rank_by_score(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank by final score only."""
        ranked = sorted(recommendations, key=lambda x: x['score'], reverse=True)
        for rank, rec in enumerate(ranked, 1):
            rec['rank'] = rank
        return ranked
    
    def _rank_by_weighted_score(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank by weighted combination of factors."""
        for rec in recommendations:
            features = rec.get('features', {})
            # Weighted score considering multiple factors
            weighted = (
                0.40 * features.get('skill_match', 0) +
                0.30 * features.get('assessment_score', 0) +
                0.20 * features.get('experience_match', 0) +
                0.10 * features.get('certification_match', 0)
            )
            rec['weighted_score'] = round(weighted, 3)
        
        ranked = sorted(recommendations, key=lambda x: x['weighted_score'], reverse=True)
        for rank, rec in enumerate(ranked, 1):
            rec['rank'] = rank
        
        return ranked
    
    def _rank_by_percentile(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank by percentile relative to all recommendations."""
        if not recommendations:
            return []
        
        scores = [r['score'] for r in recommendations]
        min_score = min(scores)
        max_score = max(scores)
        
        for rec in recommendations:
            if max_score == min_score:
                percentile = 50
            else:
                percentile = round(100 * (rec['score'] - min_score) / (max_score - min_score), 1)
            rec['percentile'] = percentile
        
        ranked = sorted(recommendations, key=lambda x: x['percentile'], reverse=True)
        for rank, rec in enumerate(ranked, 1):
            rec['rank'] = rank
        
        return ranked
    
    def get_tier_classification(self, score: float) -> str:
        """Classify recommendation into tier."""
        if score >= 0.85:
            return "TIER_A"  # Strong match - hire
        elif score >= 0.70:
            return "TIER_B"  # Good match - consider
        elif score >= 0.55:
            return "TIER_C"  # Fair match - develop
        else:
            return "TIER_D"  # Weak match - skip
    
    def group_by_tier(self, recommendations: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group recommendations by tier."""
        tiers = {
            'TIER_A': [],
            'TIER_B': [],
            'TIER_C': [],
            'TIER_D': []
        }
        
        for rec in recommendations:
            tier = self.get_tier_classification(rec['score'])
            tiers[tier].append(rec)
        
        return {k: v for k, v in tiers.items() if v}  # Only return non-empty tiers
