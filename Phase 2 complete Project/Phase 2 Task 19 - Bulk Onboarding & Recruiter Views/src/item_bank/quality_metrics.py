"""Quality Metrics Calculation Module for Task 19"""

class QualityMetricsCalculator:
    """Calculate question quality metrics."""
    
    def calculate_question_metrics(self, question_id, attempts, correct, responses_by_group=None):
        """Calculate all metrics for a question."""
        if attempts == 0:
            return {'question_id': question_id, 'attempts': 0, 'correct': 0, 
                   'correct_rate': 0, 'difficulty': 0, 'discrimination': 0, 
                   'quality_score': 0, 'classification': 'INSUFFICIENT_DATA'}
        
        correct_rate = correct / attempts
        incorrect_rate = (attempts - correct) / attempts
        difficulty = correct_rate
        discrimination = self._calculate_discrimination(correct_rate, responses_by_group) if responses_by_group else 0
        reliability = self._estimate_reliability(correct_rate, attempts)
        quality_score = self._calculate_quality_score(difficulty, discrimination, reliability)
        classification = self._classify_question(correct_rate, difficulty, discrimination)
        
        return {
            'question_id': question_id,
            'attempts': attempts,
            'correct': correct,
            'incorrect': attempts - correct,
            'correct_rate': round(correct_rate, 3),
            'incorrect_rate': round(incorrect_rate, 3),
            'difficulty': round(difficulty, 3),
            'discrimination': round(discrimination, 3),
            'reliability': round(reliability, 3),
            'quality_score': round(quality_score, 3),
            'classification': classification
        }
    
    def _calculate_discrimination(self, overall_rate, responses_by_group):
        """Calculate discrimination index."""
        if 'high_performers' not in responses_by_group or 'low_performers' not in responses_by_group:
            return 0
        
        high = responses_by_group['high_performers']
        low = responses_by_group['low_performers']
        
        if high.get('total', 0) == 0 or low.get('total', 0) == 0:
            return 0
        
        high_rate = high.get('correct', 0) / high['total']
        low_rate = low.get('correct', 0) / low['total']
        
        return max(-1, min(1, high_rate - low_rate))
    
    def _estimate_reliability(self, correct_rate, attempts):
        """Estimate reliability (item-total correlation)."""
        if attempts < 10:
            return 0
        variance = correct_rate * (1 - correct_rate)
        attempts_factor = min(1.0, attempts / 100)
        return round(variance * attempts_factor, 3)
    
    def _calculate_quality_score(self, difficulty, discrimination, reliability):
        """Calculate combined quality score."""
        if 0.40 <= difficulty <= 0.75:
            diff_score = 1.0
        elif 0.30 <= difficulty <= 0.90:
            diff_score = 0.8
        elif 0.20 <= difficulty <= 0.95:
            diff_score = 0.6
        else:
            diff_score = 0.2
        
        if discrimination >= 0.30:
            disc_score = 1.0
        elif discrimination >= 0.20:
            disc_score = 0.8
        elif discrimination >= 0.10:
            disc_score = 0.6
        else:
            disc_score = 0.2
        
        if reliability >= 0.20:
            rel_score = 1.0
        elif reliability >= 0.10:
            rel_score = 0.8
        elif reliability >= 0.05:
            rel_score = 0.6
        else:
            rel_score = 0.2
        
        quality_score = 0.30 * diff_score + 0.50 * disc_score + 0.20 * rel_score
        return round(quality_score, 3)
    
    def _classify_question(self, correct_rate, difficulty, discrimination):
        """Classify question quality."""
        if correct_rate > 0.95:
            return "TOO_EASY"
        elif correct_rate < 0.20:
            return "TOO_DIFFICULT"
        elif discrimination < 0.10:
            return "POOR_DISCRIMINATION"
        elif 0.40 <= difficulty <= 0.75 and discrimination >= 0.20:
            return "GOOD"
        elif 0.30 <= difficulty <= 0.85:
            return "ACCEPTABLE"
        else:
            return "REVIEW_NEEDED"
    
    def calculate_batch_metrics(self, questions):
        """Calculate metrics for multiple questions."""
        return [self.calculate_question_metrics(q.get('question_id'), q.get('attempts', 0), 
                q.get('correct', 0), q.get('responses_by_group')) for q in questions]
    
    def calculate_assessment_summary(self, metrics):
        """Calculate summary statistics for assessment."""
        if not metrics:
            return {'total_items': 0, 'average_difficulty': 0, 'average_discrimination': 0, 
                   'average_quality_score': 0}
        
        classifications = {}
        difficulties = []
        discriminations = []
        quality_scores = []
        
        for m in metrics:
            classifications[m.get('classification', 'UNKNOWN')] = classifications.get(m.get('classification', 'UNKNOWN'), 0) + 1
            if m.get('attempts', 0) > 0:
                difficulties.append(m.get('difficulty', 0))
                discriminations.append(m.get('discrimination', 0))
                quality_scores.append(m.get('quality_score', 0))
        
        avg_diff = sum(difficulties) / len(difficulties) if difficulties else 0
        avg_disc = sum(discriminations) / len(discriminations) if discriminations else 0
        avg_qual = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            'total_items': len(metrics),
            'average_difficulty': round(avg_diff, 3),
            'average_discrimination': round(avg_disc, 3),
            'average_quality_score': round(avg_qual, 3),
            'classification_distribution': classifications,
            'good_items': classifications.get('GOOD', 0),
            'acceptable_items': classifications.get('ACCEPTABLE', 0),
            'review_needed_items': classifications.get('REVIEW_NEEDED', 0) + 
                                  classifications.get('TOO_EASY', 0) +
                                  classifications.get('TOO_DIFFICULT', 0) +
                                  classifications.get('POOR_DISCRIMINATION', 0),
            'quality_assessment': 'EXCELLENT' if avg_qual >= 0.80 else 'GOOD' if avg_qual >= 0.70 else 'ACCEPTABLE'
        }
