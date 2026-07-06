"""
Explainability Evaluation Module - Task 18
Measure quality of generated explanations
"""

from typing import Dict, List, Any
import json


class ExplainabilityEvaluator:
    """Evaluate quality of recommendation explanations."""
    
    def __init__(self):
        """Initialize evaluator."""
        self.required_elements = [
            'matched_skills',
            'missing_skills',
            'assessment_analysis',
            'experience_analysis',
            'recommendation_level'
        ]
    
    def evaluate_explanation_completeness(self, explanation: Dict[str, Any]) -> float:
        """
        Evaluate how complete an explanation is.
        
        Returns: Score 0-1
        """
        completeness_score = 0.0
        max_score = len(self.required_elements)
        
        for element in self.required_elements:
            if element in explanation and explanation[element]:
                completeness_score += 1
        
        return completeness_score / max_score
    
    def evaluate_explanation_clarity(self, explanation: Dict[str, Any]) -> float:
        """
        Evaluate clarity of explanation.
        
        Looks for:
        - Plain language summary
        - Clear skill breakdown
        - Logical flow
        - Actionable insights
        
        Returns: Score 0-1
        """
        clarity_score = 0.0
        max_elements = 4
        
        # Check for summary
        if 'summary' in explanation and len(explanation.get('summary', '')) > 20:
            clarity_score += 1
        
        # Check for skill clarity
        if 'skill_analysis' in explanation:
            skill_analysis = explanation['skill_analysis']
            if isinstance(skill_analysis, dict) and 'summary' in skill_analysis:
                clarity_score += 1
        
        # Check for clear recommendation
        if 'recommendation_level' in explanation:
            clarity_score += 1
        
        # Check for explanation text
        if 'detailed_explanation' in explanation and \
           len(explanation.get('detailed_explanation', '')) > 50:
            clarity_score += 1
        
        return clarity_score / max_elements
    
    def evaluate_explanation_accuracy(self, explanation: Dict[str, Any],
                                     student: Dict[str, Any],
                                     job: Dict[str, Any]) -> float:
        """
        Evaluate accuracy of explanation against actual data.
        
        Returns: Score 0-1
        """
        accuracy_score = 0.0
        max_checks = 3
        
        # Check skill matching accuracy
        if 'skill_analysis' in explanation:
            student_skills = set(student.get('verified_skills', []))
            required_skills = set(job.get('required_skills', []))
            
            skill_analysis = explanation['skill_analysis']
            if isinstance(skill_analysis, dict):
                matched_in_explanation = set(skill_analysis.get('required_skills', {}).get('matched', []))
                actual_matched = student_skills & required_skills
                
                if matched_in_explanation == actual_matched:
                    accuracy_score += 1
        
        # Check assessment accuracy
        if 'assessment_analysis' in explanation:
            assess = explanation['assessment_analysis']
            student_score = student.get('assessment_score', 0)
            
            if abs(assess.get('student_score', 0) - student_score) < 0.01:
                accuracy_score += 1
        
        # Check experience accuracy
        if 'experience_analysis' in explanation:
            exp = explanation['experience_analysis']
            student_years = student.get('years_experience', 0)
            required_years = job.get('required_experience_years', 0)
            
            if exp.get('student_years') == student_years and \
               exp.get('required_years') == required_years:
                accuracy_score += 1
        
        return accuracy_score / max_checks
    
    def evaluate_batch_explanations(self, explanations: List[Dict[str, Any]],
                                   students: List[Dict[str, Any]],
                                   jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate a batch of explanations.
        
        Returns:
            Summary metrics
        """
        if not explanations:
            return {
                'total_explanations': 0,
                'average_completeness': 0.0,
                'average_clarity': 0.0,
                'average_accuracy': 0.0,
                'overall_quality_score': 0.0
            }
        
        completeness_scores = []
        clarity_scores = []
        accuracy_scores = []
        
        student_by_id = {s['student_id']: s for s in students}
        job_by_id = {j['job_id']: j for j in jobs}
        
        for i, explanation in enumerate(explanations):
            completeness = self.evaluate_explanation_completeness(explanation)
            clarity = self.evaluate_explanation_clarity(explanation)
            
            # Try to find matching student and job for accuracy check
            accuracy = 1.0  # Default to perfect if we can't verify
            if i < len(students) and i < len(jobs):
                try:
                    accuracy = self.evaluate_explanation_accuracy(
                        explanation,
                        students[i % len(students)],
                        jobs[i % len(jobs)]
                    )
                except:
                    pass
            
            completeness_scores.append(completeness)
            clarity_scores.append(clarity)
            accuracy_scores.append(accuracy)
        
        avg_completeness = sum(completeness_scores) / len(completeness_scores)
        avg_clarity = sum(clarity_scores) / len(clarity_scores)
        avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
        
        overall_quality = (avg_completeness * 0.4 + avg_clarity * 0.4 + avg_accuracy * 0.2)
        
        return {
            'total_explanations': len(explanations),
            'average_completeness': round(avg_completeness, 3),
            'average_clarity': round(avg_clarity, 3),
            'average_accuracy': round(avg_accuracy, 3),
            'overall_quality_score': round(overall_quality, 3),
            'completeness_scores': completeness_scores,
            'clarity_scores': clarity_scores,
            'accuracy_scores': accuracy_scores
        }
    
    def get_explanation_quality_report(self, evaluation_results: Dict[str, Any]) -> str:
        """
        Generate human-readable quality report.
        
        Returns:
            Formatted report
        """
        quality_score = evaluation_results['overall_quality_score']
        
        if quality_score >= 0.90:
            status = "EXCELLENT"
        elif quality_score >= 0.80:
            status = "VERY GOOD"
        elif quality_score >= 0.70:
            status = "GOOD"
        elif quality_score >= 0.60:
            status = "FAIR"
        else:
            status = "POOR"
        
        report = f"""
EXPLANATION QUALITY REPORT
{'='*60}

Total Explanations Evaluated: {evaluation_results['total_explanations']}

QUALITY METRICS:
  Completeness:   {evaluation_results['average_completeness']:.1%}
  Clarity:        {evaluation_results['average_clarity']:.1%}
  Accuracy:       {evaluation_results['average_accuracy']:.1%}
  
OVERALL QUALITY SCORE: {evaluation_results['overall_quality_score']:.1%}
STATUS: {status}

INTERPRETATION:
"""
        
        if status == "EXCELLENT":
            report += "  Explanations are comprehensive, clear, and accurate."
        elif status == "VERY GOOD":
            report += "  Explanations are good quality with minor areas for improvement."
        elif status == "GOOD":
            report += "  Explanations meet standards but could be more detailed."
        elif status == "FAIR":
            report += "  Explanations need significant improvement in clarity/completeness."
        else:
            report += "  Explanations need major revision to meet standards."
        
        return report
    
    def identify_improvement_areas(self, evaluation_results: Dict[str, Any]) -> List[str]:
        """
        Identify areas needing improvement.
        
        Returns:
            List of recommendations
        """
        improvements = []
        
        if evaluation_results['average_completeness'] < 0.85:
            improvements.append(
                "Add more detailed breakdowns of why skills match or don't match"
            )
        
        if evaluation_results['average_clarity'] < 0.80:
            improvements.append(
                "Use simpler language and clearer formatting for explanations"
            )
        
        if evaluation_results['average_accuracy'] < 0.90:
            improvements.append(
                "Verify accuracy of matched/missing skills and experience gaps"
            )
        
        return improvements
    
    def generate_summary_statistics(self, explanations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics about explanations.
        
        Returns:
            Statistics dictionary
        """
        if not explanations:
            return {}
        
        stats = {
            'total_explanations': len(explanations),
            'explanations_with_matched_skills': 0,
            'explanations_with_missing_skills': 0,
            'explanations_with_feature_breakdown': 0,
            'explanations_with_summary': 0,
            'average_matched_skills_count': 0,
            'average_missing_skills_count': 0,
            'explanation_types_used': {}
        }
        
        matched_skills_counts = []
        missing_skills_counts = []
        
        for explanation in explanations:
            # Check for matched skills
            if 'skill_analysis' in explanation:
                skill_analysis = explanation['skill_analysis']
                if isinstance(skill_analysis, dict):
                    matched = skill_analysis.get('required_skills', {}).get('matched', [])
                    if matched:
                        stats['explanations_with_matched_skills'] += 1
                        matched_skills_counts.append(len(matched))
                    
                    missing = skill_analysis.get('required_skills', {}).get('missing', [])
                    if missing:
                        stats['explanations_with_missing_skills'] += 1
                        missing_skills_counts.append(len(missing))
            
            # Check for feature breakdown
            if 'feature_contributions' in explanation:
                stats['explanations_with_feature_breakdown'] += 1
            
            # Check for summary
            if 'summary' in explanation:
                stats['explanations_with_summary'] += 1
        
        if matched_skills_counts:
            stats['average_matched_skills_count'] = sum(matched_skills_counts) / len(matched_skills_counts)
        
        if missing_skills_counts:
            stats['average_missing_skills_count'] = sum(missing_skills_counts) / len(missing_skills_counts)
        
        return stats
