"""
Ranking module for Recommendation Engine v1
Includes baseline implementation and metrics evaluation
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score
import logging

logger = logging.getLogger(__name__)


class BaselineRecommender:
    """
    Baseline recommender: Simple skill overlap matching
    Serves as a benchmark against which to measure Rec v1
    """
    
    def __init__(self, students_df: pd.DataFrame, jobs_df: pd.DataFrame):
        self.students = students_df.copy()
        self.jobs = jobs_df.copy()
        self._preprocess_data()
    
    def _preprocess_data(self):
        """Preprocess skill strings into lists"""
        self.students['skills_list'] = self.students['verified_skills'].apply(
            lambda x: [s.strip().lower() for s in str(x).split(',')]
        )
        self.jobs['required_skills_list'] = self.jobs['required_skills'].apply(
            lambda x: [s.strip().lower() for s in str(x).split(',')]
        )
    
    def score_match(self, student_skills: List[str], job_skills: List[str]) -> float:
        """
        Calculate skill overlap ratio
        
        Returns:
            Percentage of required skills matched by student
        """
        student_skills_set = set(student_skills)
        job_skills_set = set(job_skills)
        
        matched = len(student_skills_set.intersection(job_skills_set))
        required = len(job_skills_set)
        
        if required == 0:
            return 1.0
        
        return matched / required
    
    def recommend_jobs(self, student_id: int, top_n: int = 5) -> List[Dict]:
        """
        Simple baseline: rank jobs by skill overlap
        
        Returns:
            List of (job_id, job_title, skill_match_score)
        """
        student = self.students[self.students['student_id'] == student_id]
        if student.empty:
            return []
        
        student = student.iloc[0]
        recommendations = []
        
        for _, job in self.jobs.iterrows():
            score = self.score_match(
                student['skills_list'],
                job['required_skills_list']
            )
            recommendations.append({
                'job_id': job['job_id'],
                'job_title': job['title'],
                'baseline_score': score
            })
        
        recommendations.sort(key=lambda x: x['baseline_score'], reverse=True)
        return recommendations[:top_n]


class MetricsEvaluator:
    """
    Evaluate recommendation system using standard ML metrics
    Computes precision, recall, false positive rate on real data
    """
    
    def __init__(self):
        self.metrics = {}
    
    def _generate_ground_truth(self, students: pd.DataFrame, 
                               jobs: pd.DataFrame,
                               threshold: float = 0.75) -> pd.DataFrame:
        """
        Generate ground truth labels based on heuristic matching
        
        A job is "good fit" for student if:
        - At least 80% of required skills are matched
        - Experience requirement is met or exceeded
        - Education meets requirement
        
        Args:
            students: Student dataframe
            jobs: Jobs dataframe
            threshold: Overall fit threshold
            
        Returns:
            DataFrame with columns: student_id, job_id, is_good_fit
        """
        students = students.copy()
        students['skills_list'] = students['verified_skills'].apply(
            lambda x: [s.strip().lower() for s in str(x).split(',')]
        )
        
        jobs = jobs.copy()
        jobs['required_skills_list'] = jobs['required_skills'].apply(
            lambda x: [s.strip().lower() for s in str(x).split(',')]
        )
        
        ground_truth = []
        
        for _, student in students.iterrows():
            for _, job in jobs.iterrows():
                # Calculate fit criteria
                student_skills_set = set(student['skills_list'])
                job_skills_set = set(job['required_skills_list'])
                skill_match = len(student_skills_set.intersection(job_skills_set)) / len(job_skills_set) if job_skills_set else 1.0
                
                exp_ok = student['years_experience'] >= job['required_experience']
                
                edu_hierarchy = {"high school": 1, "bachelor's": 2, "master's": 3, "phd": 4}
                student_level = next((edu_hierarchy.get(k, 0) for k in edu_hierarchy if k.lower() in student['education_level'].lower()), 0)
                job_level = next((edu_hierarchy.get(k, 0) for k in edu_hierarchy if k.lower() in job['education_requirement'].lower()), 0)
                edu_ok = student_level >= job_level
                
                # Label as good fit if meets most criteria
                is_good_fit = skill_match >= 0.75 and exp_ok and edu_ok
                
                ground_truth.append({
                    'student_id': student['student_id'],
                    'job_id': job['job_id'],
                    'is_good_fit': int(is_good_fit)
                })
        
        return pd.DataFrame(ground_truth)
    
    def evaluate_predictions(self, y_true: np.ndarray, y_pred: np.ndarray, 
                            y_pred_proba: np.ndarray = None) -> Dict[str, float]:
        """
        Evaluate prediction quality using standard metrics
        
        Args:
            y_true: Ground truth binary labels
            y_pred: Predicted binary labels
            y_pred_proba: Predicted probabilities (optional, for AUC)
            
        Returns:
            Dictionary of metrics
        """
        metrics = {
            'precision': precision_score(y_true, y_pred, zero_division=0),
            'recall': recall_score(y_true, y_pred, zero_division=0),
            'f1': f1_score(y_true, y_pred, zero_division=0),
            'false_positive_rate': np.sum((y_pred == 1) & (y_true == 0)) / np.sum(y_true == 0) if np.sum(y_true == 0) > 0 else 0,
            'true_negative_rate': np.sum((y_pred == 0) & (y_true == 0)) / np.sum(y_true == 0) if np.sum(y_true == 0) > 0 else 0,
        }
        
        if y_pred_proba is not None:
            try:
                metrics['auc'] = roc_auc_score(y_true, y_pred_proba)
            except:
                metrics['auc'] = None
        
        return metrics
    
    def evaluate_recommendation_quality(self, recommendations: List[Dict],
                                       ground_truth: pd.DataFrame) -> Dict:
        """
        Evaluate quality of recommendations against ground truth
        
        Args:
            recommendations: List of recommendation dicts with job_id and score
            ground_truth: DataFrame with student_id, job_id, is_good_fit
            
        Returns:
            Evaluation metrics
        """
        # Create binary predictions from recommendations
        # Top 5 recommendations = positive predictions
        y_true_list = []
        y_pred_list = []
        y_pred_proba_list = []
        
        for rec in recommendations:
            student_id = rec.get('student_id')
            job_id = rec.get('job_id')
            score = rec.get('score', rec.get('overall_score', 0))
            
            # Find ground truth
            gt = ground_truth[(ground_truth['student_id'] == student_id) & 
                             (ground_truth['job_id'] == job_id)]
            
            if not gt.empty:
                y_true = gt.iloc[0]['is_good_fit']
                y_pred = 1 if rec.get('rank', 999) <= 5 else 0
                
                y_true_list.append(y_true)
                y_pred_list.append(y_pred)
                y_pred_proba_list.append(score)
        
        if not y_true_list:
            return {'error': 'No matching records in ground truth'}
        
        y_true = np.array(y_true_list)
        y_pred = np.array(y_pred_list)
        y_pred_proba = np.array(y_pred_proba_list)
        
        return self.evaluate_predictions(y_true, y_pred, y_pred_proba)


class RecommendationComparison:
    """
    Compare baseline vs Rec v1 to show improvement
    """
    
    def __init__(self, baseline_metrics: Dict, rec_v1_metrics: Dict):
        self.baseline = baseline_metrics
        self.rec_v1 = rec_v1_metrics
    
    def get_comparison(self) -> Dict:
        """
        Generate comparison report showing improvement
        
        Returns:
            Dictionary with metrics for both systems and deltas
        """
        comparison = {
            'baseline': self.baseline,
            'rec_v1': self.rec_v1,
            'improvement': {}
        }
        
        for key in self.baseline:
            if key not in self.rec_v1 or self.rec_v1[key] is None:
                continue
            
            delta = self.rec_v1[key] - self.baseline[key]
            percent_improvement = (delta / self.baseline[key] * 100) if self.baseline[key] != 0 else 0
            
            comparison['improvement'][key] = {
                'delta': round(delta, 3),
                'percent_improvement': round(percent_improvement, 1)
            }
        
        return comparison
    
    def print_comparison(self):
        """Pretty print comparison results"""
        comparison = self.get_comparison()
        
        print("\n" + "="*80)
        print("RECOMMENDATION ENGINE: BASELINE vs REC V1 COMPARISON")
        print("="*80)
        
        print("\nBASELINE METRICS (Skill Overlap Only):")
        for key, value in self.baseline.items():
            print(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")
        
        print("\nREC V1 METRICS (Multi-Factor):")
        for key, value in self.rec_v1.items():
            print(f"  {key}: {value:.3f}" if isinstance(value, float) else f"  {key}: {value}")
        
        print("\nIMPROVEMENT (Rec V1 vs Baseline):")
        for key, improvement in comparison['improvement'].items():
            delta = improvement['delta']
            percent = improvement['percent_improvement']
            symbol = "↑" if delta > 0 else "↓"
            print(f"  {key}: {symbol} {abs(delta):+.3f} ({percent:+.1f}%)")
        
        print("\n" + "="*80)
