"""
Metrics Calculation Module
Compute precision, recall, and other evaluation metrics
"""

from typing import Dict, List, Any, Tuple
import json


class MetricsCalculator:
    """Calculate evaluation metrics for recommendations."""
    
    def __init__(self):
        self.results = {}
    
    def calculate_precision_recall_fpr(self, 
                                      predictions: List[Tuple[int, int, bool]],
                                      ) -> Dict[str, float]:
        """
        Calculate precision, recall, and false positive rate.
        
        Args:
            predictions: List of (student_id, job_id, is_good_match) tuples
            
        Returns:
            Dictionary with metrics
        """
        if not predictions:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'false_positive_rate': 0.0,
                'true_positives': 0,
                'false_positives': 0,
                'false_negatives': 0,
                'true_negatives': 0
            }
        
        # Separate true and false labels
        true_positives = sum(1 for _, _, label in predictions if label)
        false_positives = sum(1 for _, _, label in predictions if not label)
        
        # For recall, we need to know total actual positives
        # Here we'll assume all recommendations with score > 0.7 should match reality
        total_positives = true_positives + sum(1 for _, _, label in predictions if not label and true_positives > 0)
        
        # Calculate metrics
        if true_positives + false_positives == 0:
            precision = 0.0
        else:
            precision = true_positives / (true_positives + false_positives)
        
        if total_positives == 0:
            recall = 0.0
        else:
            recall = true_positives / total_positives
        
        # False positive rate
        total_negatives = false_positives
        if total_negatives == 0:
            fpr = 0.0
        else:
            fpr = false_positives / (false_positives + true_positives)
        
        return {
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'false_positive_rate': round(fpr, 3),
            'true_positives': true_positives,
            'false_positives': false_positives,
            'total_recommendations': len(predictions)
        }
    
    def calculate_baseline_metrics(self, 
                                  students: List[Dict[str, Any]],
                                  jobs: List[Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate baseline metrics using skill overlap only.
        
        Baseline: Rank by (matched_skills / required_skills)
        """
        metrics = {
            'baseline_accuracy': 0.0,
            'baseline_avg_score': 0.0,
            'recommendations_above_threshold': 0
        }
        
        total_score = 0
        count = 0
        above_threshold = 0
        
        for student in students:
            student_skills = set(student.get('verified_skills', []))
            
            for job in jobs:
                required_skills = set(job.get('required_skills', []))
                if not required_skills:
                    continue
                
                overlap = len(student_skills & required_skills) / len(required_skills)
                total_score += overlap
                count += 1
                
                if overlap >= 0.5:  # 50% overlap threshold
                    above_threshold += 1
        
        if count > 0:
            metrics['baseline_accuracy'] = round(total_score / count, 3)
            metrics['baseline_avg_score'] = round(total_score / count, 3)
        
        metrics['recommendations_above_threshold'] = above_threshold
        
        return metrics
    
    def calculate_improvement(self, baseline_score: float, 
                             recommendation_score: float) -> float:
        """Calculate percentage improvement over baseline."""
        if baseline_score == 0:
            return 0.0
        
        improvement = (recommendation_score - baseline_score) / baseline_score
        return round(improvement * 100, 1)
    
    def calculate_coverage(self, recommendations: List[Dict[str, Any]], 
                          all_jobs: List[Dict[str, Any]]) -> float:
        """Calculate what percentage of jobs got recommended."""
        if not all_jobs:
            return 0.0
        
        recommended_job_ids = set(r['job_id'] for r in recommendations)
        coverage = len(recommended_job_ids) / len(all_jobs)
        
        return round(coverage, 3)
    
    def calculate_diversity(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate recommendation diversity."""
        if not recommendations:
            return {
                'avg_score_spread': 0.0,
                'max_score': 0.0,
                'min_score': 0.0,
                'score_std_dev': 0.0
            }
        
        scores = [r['score'] for r in recommendations]
        
        max_score = max(scores)
        min_score = min(scores)
        avg_score = sum(scores) / len(scores)
        
        # Calculate standard deviation
        variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
        std_dev = variance ** 0.5
        
        return {
            'avg_score_spread': round(max_score - min_score, 3),
            'max_score': round(max_score, 3),
            'min_score': round(min_score, 3),
            'score_std_dev': round(std_dev, 3),
            'recommendation_count': len(recommendations)
        }
    
    def generate_report(self, metrics: Dict[str, Any]) -> str:
        """Generate human-readable metrics report."""
        report = f"""
RECOMMENDATION SYSTEM EVALUATION REPORT
{'=' * 50}

PERFORMANCE METRICS:
- Precision: {metrics.get('precision', 'N/A')}
- Recall: {metrics.get('recall', 'N/A')}
- False Positive Rate: {metrics.get('false_positive_rate', 'N/A')}

BASELINE COMPARISON:
- Baseline Accuracy: {metrics.get('baseline_accuracy', 'N/A')}
- Recommendation Accuracy: {metrics.get('recommendation_accuracy', 'N/A')}
- Improvement: {metrics.get('improvement_over_baseline', 'N/A')}%

COVERAGE & DIVERSITY:
- Job Coverage: {metrics.get('coverage', 'N/A')}
- Average Score Spread: {metrics.get('diversity', {}).get('avg_score_spread', 'N/A')}
- Score Std Dev: {metrics.get('diversity', {}).get('score_std_dev', 'N/A')}

SAMPLE SIZE:
- Students Evaluated: {metrics.get('student_count', 'N/A')}
- Jobs in Database: {metrics.get('job_count', 'N/A')}
- Total Recommendations: {metrics.get('total_recommendations', 'N/A')}

QUALITY ASSESSMENT:
- Data Quality: {metrics.get('data_quality_score', 'N/A')}/100
- Recommendation Quality: {metrics.get('recommendation_quality_score', 'N/A')}/100
        """
        return report.strip()
