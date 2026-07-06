"""
Main Evaluator Module
End-to-end evaluation of recommendation system
"""

import json
from typing import Dict, List, Any
from .metrics import MetricsCalculator
from ..recommendation import RecommendationEngine, ExplainabilityEngine, GuardrailValidator
from ..parsing import ResumeParser, JDParser


class Evaluator:
    """End-to-end evaluation of recommendation system."""
    
    def __init__(self):
        self.metrics_calculator = MetricsCalculator()
        self.recommendation_engine = RecommendationEngine()
        self.explainability_engine = ExplainabilityEngine()
        self.guardrail_validator = GuardrailValidator()
        self.results = {}
    
    def evaluate_system(self, students: List[Dict[str, Any]], 
                       jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run complete evaluation of recommendation system.
        
        Args:
            students: List of student profiles
            jobs: List of job profiles
            
        Returns:
            Comprehensive evaluation report
        """
        # Load data
        self.recommendation_engine.load_students(students)
        self.recommendation_engine.load_jobs(jobs)
        
        # Generate recommendations
        student_ids = [s['student_id'] for s in students]
        all_recommendations = self.recommendation_engine.batch_recommend(student_ids, top_k=len(jobs))
        
        # Calculate metrics
        baseline_metrics = self.metrics_calculator.calculate_baseline_metrics(students, jobs)
        
        total_recs = sum(len(recs) for recs in all_recommendations.values())
        rec_accuracy = sum(r['score'] for recs in all_recommendations.values() for r in recs) / total_recs if total_recs > 0 else 0
        
        improvement = self.metrics_calculator.calculate_improvement(
            baseline_metrics['baseline_accuracy'],
            rec_accuracy
        )
        
        # Validate recommendations
        all_recs_flat = []
        for recs in all_recommendations.values():
            all_recs_flat.extend(recs)
        
        quality_metrics = self.guardrail_validator.validate_batch(
            students, jobs,
            {(r['student_id'], r['job_id']): r['score'] for r in all_recs_flat}
        )
        
        diversity_metrics = self.metrics_calculator.calculate_diversity(all_recs_flat)
        
        # Compile report
        report = {
            'evaluation_date': '2024-01-15',
            'sample_size': {
                'students': len(students),
                'jobs': len(jobs),
                'total_student_job_pairs': len(students) * len(jobs)
            },
            'baseline_metrics': baseline_metrics,
            'recommendation_metrics': {
                'accuracy': round(rec_accuracy, 3),
                'improvement_over_baseline': f"{improvement}%",
                'total_recommendations': total_recs
            },
            'quality_metrics': quality_metrics,
            'diversity_metrics': diversity_metrics,
            'recommendation_tier_distribution': self._get_tier_distribution(all_recs_flat),
            'data_quality_score': self._calculate_data_quality_score(students, jobs),
            'system_readiness': self._assess_system_readiness(
                quality_metrics, improvement, rec_accuracy
            )
        }
        
        self.results = report
        return report
    
    def _get_tier_distribution(self, recommendations: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of recommendations by tier."""
        from ..recommendation import RankingEngine
        ranking_engine = RankingEngine()
        
        tiers = {'TIER_A': 0, 'TIER_B': 0, 'TIER_C': 0, 'TIER_D': 0}
        
        for rec in recommendations:
            tier = ranking_engine.get_tier_classification(rec['score'])
            tiers[tier] += 1
        
        return {k: v for k, v in tiers.items() if v > 0}
    
    def _calculate_data_quality_score(self, students: List[Dict[str, Any]], 
                                     jobs: List[Dict[str, Any]]) -> int:
        """Calculate overall data quality score (0-100)."""
        score = 100
        
        # Check students
        students_with_skills = sum(1 for s in students if s.get('verified_skills'))
        if students_with_skills < len(students) * 0.9:
            score -= 10
        
        students_with_assessment = sum(1 for s in students if s.get('assessment_score'))
        if students_with_assessment < len(students) * 0.8:
            score -= 10
        
        # Check jobs
        jobs_with_requirements = sum(1 for j in jobs if j.get('required_skills'))
        if jobs_with_requirements < len(jobs) * 0.95:
            score -= 10
        
        return max(0, score)
    
    def _assess_system_readiness(self, quality_metrics: Dict[str, Any], 
                                improvement: float, accuracy: float) -> str:
        """Assess if system is ready for production."""
        issues = []
        
        if quality_metrics.get('validity_rate', '0%').rstrip('%') < '90':
            issues.append("Data quality below 90%")
        
        if improvement < 20:
            issues.append("Improvement over baseline insufficient")
        
        if accuracy < 0.70:
            issues.append("Overall accuracy below 70%")
        
        if not issues:
            return "READY_FOR_PRODUCTION"
        elif len(issues) <= 1:
            return "READY_WITH_CAVEATS"
        else:
            return "NOT_READY"
    
    def generate_summary_report(self) -> str:
        """Generate human-readable summary report."""
        if not self.results:
            return "No evaluation results available"
        
        report = f"""
RECOMMENDATION SYSTEM EVALUATION REPORT
{'=' * 70}

EVALUATION DATE: {self.results.get('evaluation_date')}

SAMPLE SIZE:
  - Students: {self.results['sample_size']['students']}
  - Jobs: {self.results['sample_size']['jobs']}
  - Student-Job Pairs: {self.results['sample_size']['total_student_job_pairs']}

BASELINE METRICS:
  - Baseline Accuracy (Skill Overlap): {self.results['baseline_metrics'].get('baseline_accuracy', 'N/A')}
  - Recommendations Above Threshold: {self.results['baseline_metrics'].get('recommendations_above_threshold', 'N/A')}

RECOMMENDATION v1 PERFORMANCE:
  - Accuracy: {self.results['recommendation_metrics'].get('accuracy', 'N/A')}
  - Improvement Over Baseline: {self.results['recommendation_metrics'].get('improvement_over_baseline', 'N/A')}
  - Total Recommendations Generated: {self.results['recommendation_metrics'].get('total_recommendations', 'N/A')}

QUALITY METRICS:
  - Valid Recommendations: {self.results['quality_metrics'].get('valid', 0)}/{self.results['quality_metrics'].get('total', 0)}
  - Validity Rate: {self.results['quality_metrics'].get('validity_rate', 'N/A')}

DIVERSITY METRICS:
  - Average Score Spread: {self.results['diversity_metrics'].get('avg_score_spread', 'N/A')}
  - Score Std Dev: {self.results['diversity_metrics'].get('score_std_dev', 'N/A')}

TIER DISTRIBUTION:
  - TIER_A (Strong Match): {self.results['recommendation_tier_distribution'].get('TIER_A', 0)}
  - TIER_B (Good Match): {self.results['recommendation_tier_distribution'].get('TIER_B', 0)}
  - TIER_C (Fair Match): {self.results['recommendation_tier_distribution'].get('TIER_C', 0)}
  - TIER_D (Weak Match): {self.results['recommendation_tier_distribution'].get('TIER_D', 0)}

DATA QUALITY SCORE: {self.results.get('data_quality_score', 0)}/100

SYSTEM READINESS: {self.results.get('system_readiness')}

{'=' * 70}
        """
        return report.strip()
    
    def save_report(self, output_path: str) -> None:
        """Save evaluation report to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
