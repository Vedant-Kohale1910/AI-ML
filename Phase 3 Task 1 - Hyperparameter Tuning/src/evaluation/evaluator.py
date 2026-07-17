"""Model Evaluator - Task 9"""
from typing import Dict, Any

class ModelEvaluator:
    """Compare baseline and tuned models."""
    
    @staticmethod
    def compare_metrics(baseline: Dict[str, float],
                       tuned: Dict[str, float]) -> Dict[str, Any]:
        """Compare baseline vs tuned metrics."""
        comparison = {}
        
        for metric in baseline:
            if metric in tuned:
                improvement = tuned[metric] - baseline[metric]
                improvement_pct = (improvement / baseline[metric] * 100) if baseline[metric] != 0 else 0
                
                comparison[metric] = {
                    'baseline': baseline[metric],
                    'tuned': tuned[metric],
                    'improvement': improvement,
                    'improvement_pct': improvement_pct
                }
        
        return comparison
    
    @staticmethod
    def verify_no_overfitting(cv_score: float, test_score: float,
                             threshold: float = 0.05) -> bool:
        """Verify model is not overfitting."""
        gap = abs(cv_score - test_score)
        return gap < threshold
    
    @staticmethod
    def generate_report(baseline_metrics: Dict[str, float],
                       tuned_metrics: Dict[str, float],
                       cv_results: Dict[str, Any]) -> str:
        """Generate comprehensive evaluation report."""
        comparison = ModelEvaluator.compare_metrics(baseline_metrics, tuned_metrics)
        
        report = """
HYPERPARAMETER TUNING EVALUATION REPORT
================================================================================

BASELINE MODEL PERFORMANCE:
"""
        for metric, value in baseline_metrics.items():
            report += f"  {metric}: {value:.4f}\n"
        
        report += "\nTUNED MODEL PERFORMANCE:\n"
        for metric, value in tuned_metrics.items():
            report += f"  {metric}: {value:.4f}\n"
        
        report += "\nIMPROVEMENT:\n"
        for metric, details in comparison.items():
            report += f"  {metric}: {details['improvement']:+.4f} ({details['improvement_pct']:+.1f}%)\n"
        
        report += "\n" + "="*80
        
        return report
