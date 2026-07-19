"""
Weak Item Detector - Task 19
Identify and flag problematic assessment questions
"""

from typing import Dict, List, Any


class WeakItemDetector:
    """Detect problematic assessment items."""
    
    def __init__(self, rules: Dict[str, Any]):
        """
        Initialize detector with rules.
        
        Args:
            rules: Dictionary containing thresholds
        """
        self.rules = rules
    
    def detect_weak_items(self, question_stats: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Detect weak items from question statistics.
        
        Args:
            question_stats: List of statistics for each question
            
        Returns:
            Analysis results
        """
        weak_items = []
        good_items = []
        
        for stats in question_stats:
            result = self._classify_item(stats)
            
            if result['status'] == 'WEAK':
                weak_items.append(result)
            else:
                good_items.append(result)
        
        return {
            'total_items': len(question_stats),
            'weak_items': weak_items,
            'good_items': good_items,
            'weak_count': len(weak_items),
            'good_count': len(good_items),
            'summary': self._generate_summary(weak_items, good_items)
        }
    
    def _classify_item(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Classify a single item as weak or good."""
        correct_rate = stats.get('correct_rate', 0)
        discrimination = stats.get('discrimination_index', 0)
        
        # Determine issue type
        issue_type = None
        risk_level = "GREEN"  # Good
        confidence = 0.0
        
        # Check if too easy
        if correct_rate >= self.rules.get('too_easy_threshold', 0.95):
            issue_type = "TOO_EASY"
            risk_level = "RED"
            confidence = min(1.0, (correct_rate - 0.95) / 0.05)
        
        # Check if too difficult
        elif correct_rate <= self.rules.get('too_difficult_threshold', 0.20):
            issue_type = "TOO_DIFFICULT"
            risk_level = "RED"
            confidence = min(1.0, (0.20 - correct_rate) / 0.20)
        
        # Check discrimination (only if not already flagged)
        elif discrimination < self.rules.get('poor_discrimination_threshold', 0.20):
            issue_type = "LOW_DISCRIMINATION"
            risk_level = "YELLOW"
            confidence = 0.6 + (discrimination * 0.2)
        
        status = "WEAK" if issue_type else "GOOD"
        
        return {
            'question_id': stats['question_id'],
            'status': status,
            'issue_type': issue_type,
            'risk_level': risk_level,
            'correct_rate': stats['correct_rate'],
            'correct_percentage': stats['correct_percentage'],
            'discrimination_index': stats['discrimination_index'],
            'difficulty_level': stats['difficulty_level'],
            'confidence': round(confidence, 2),
            'total_attempts': stats['total_attempts'],
            'reasoning': self._get_reasoning(stats, issue_type)
        }
    
    def _get_reasoning(self, stats: Dict[str, Any], issue_type: str) -> str:
        """Generate reasoning for classification."""
        if issue_type == "TOO_EASY":
            return f"Only {100 - stats['correct_percentage']}% of students answered incorrectly. Cannot differentiate."
        elif issue_type == "TOO_DIFFICULT":
            return f"Only {stats['correct_percentage']}% of students answered correctly. May be flawed."
        elif issue_type == "LOW_DISCRIMINATION":
            return "This question does not effectively differentiate between strong and weak students."
        else:
            return "Question performs well in assessments."
    
    def _generate_summary(self, weak_items: List[Dict[str, Any]], 
                         good_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary statistics."""
        too_easy = sum(1 for item in weak_items if item['issue_type'] == 'TOO_EASY')
        too_difficult = sum(1 for item in weak_items if item['issue_type'] == 'TOO_DIFFICULT')
        low_disc = sum(1 for item in weak_items if item['issue_type'] == 'LOW_DISCRIMINATION')
        
        red_items = sum(1 for item in weak_items if item['risk_level'] == 'RED')
        yellow_items = sum(1 for item in weak_items if item['risk_level'] == 'YELLOW')
        
        return {
            'total_weak': len(weak_items),
            'total_good': len(good_items),
            'too_easy_count': too_easy,
            'too_difficult_count': too_difficult,
            'low_discrimination_count': low_disc,
            'critical_items': red_items,
            'review_items': yellow_items,
            'quality_percentage': round(100 * len(good_items) / (len(good_items) + len(weak_items)), 1)
        }
    
    def get_flagged_items(self, analysis: Dict[str, Any], 
                         risk_level: str = None) -> List[Dict[str, Any]]:
        """Get flagged items, optionally filtered by risk level."""
        items = analysis.get('weak_items', [])
        
        if risk_level:
            items = [item for item in items if item['risk_level'] == risk_level]
        
        return sorted(items, key=lambda x: x['confidence'], reverse=True)
