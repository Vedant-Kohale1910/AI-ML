"""
Item Bank Analyzer - Task 19
Compute statistics for assessment questions
"""

from typing import Dict, List, Any
import json


class ItemAnalyzer:
    """Analyze assessment question performance."""
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    def analyze_question(self, question_id: str, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze performance of a single question.
        
        Args:
            question_id: Question identifier
            responses: List of student responses
            
        Returns:
            Statistics dictionary
        """
        if not responses:
            return self._empty_stats(question_id)
        
        correct_count = sum(1 for r in responses if r.get('is_correct', False))
        incorrect_count = len(responses) - correct_count
        total = len(responses)
        
        correct_rate = correct_count / total if total > 0 else 0
        
        stats = {
            'question_id': question_id,
            'total_attempts': total,
            'correct_count': correct_count,
            'incorrect_count': incorrect_count,
            'correct_rate': round(correct_rate, 3),
            'correct_percentage': round(correct_rate * 100, 1),
            'difficulty_level': self._get_difficulty_level(correct_rate),
            'discrimination_index': self._calculate_discrimination(responses),
            'avg_time_seconds': self._calculate_avg_time(responses),
            'response_distribution': self._get_response_distribution(responses)
        }
        
        return stats
    
    def _empty_stats(self, question_id: str) -> Dict[str, Any]:
        """Return empty statistics."""
        return {
            'question_id': question_id,
            'total_attempts': 0,
            'correct_count': 0,
            'incorrect_count': 0,
            'correct_rate': 0,
            'difficulty_level': 'Unknown',
            'error': 'No data available'
        }
    
    def _get_difficulty_level(self, correct_rate: float) -> str:
        """Map correct rate to difficulty level."""
        if correct_rate >= 0.85:
            return "Very Easy"
        elif correct_rate >= 0.65:
            return "Easy"
        elif correct_rate >= 0.35:
            return "Medium"
        elif correct_rate >= 0.15:
            return "Hard"
        else:
            return "Very Hard"
    
    def _calculate_discrimination(self, responses: List[Dict[str, Any]]) -> float:
        """
        Calculate discrimination index.
        
        Higher discrimination = better at differentiating strong/weak students
        """
        if len(responses) < 2:
            return 0.0
        
        # Sort by student ability (approximated by overall score)
        # For now, simple approach: correlation between this Q and overall performance
        correct_flags = [1 if r.get('is_correct', False) else 0 for r in responses]
        
        # Simple discrimination: variance of correct answers
        if not correct_flags or len(set(correct_flags)) == 1:
            return 0.0
        
        mean = sum(correct_flags) / len(correct_flags)
        variance = sum((x - mean) ** 2 for x in correct_flags) / len(correct_flags)
        
        return round(variance, 3)
    
    def _calculate_avg_time(self, responses: List[Dict[str, Any]]) -> float:
        """Calculate average time spent on question."""
        times = [r.get('time_seconds', 0) for r in responses if r.get('time_seconds')]
        
        if not times:
            return 0.0
        
        return round(sum(times) / len(times), 1)
    
    def _get_response_distribution(self, responses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of answer choices (if available)."""
        distribution = {}
        
        for response in responses:
            answer = response.get('selected_option', 'Unknown')
            distribution[answer] = distribution.get(answer, 0) + 1
        
        return distribution
    
    def analyze_batch(self, questions_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Analyze multiple questions.
        
        Args:
            questions_data: Dict mapping question_id to list of responses
            
        Returns:
            List of statistics for each question
        """
        results = []
        
        for question_id, responses in questions_data.items():
            stats = self.analyze_question(question_id, responses)
            results.append(stats)
        
        return results


def load_and_analyze_assessment_results(results_path: str) -> List[Dict[str, Any]]:
    """Load assessment results and analyze all questions."""
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    analyzer = ItemAnalyzer()
    
    # Group responses by question
    questions_data = {}
    for response in data.get('responses', []):
        q_id = response['question_id']
        if q_id not in questions_data:
            questions_data[q_id] = []
        questions_data[q_id].append(response)
    
    return analyzer.analyze_batch(questions_data)
