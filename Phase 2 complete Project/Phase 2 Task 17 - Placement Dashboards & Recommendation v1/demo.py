#!/usr/bin/env python3
"""
Demo Script
End-to-end demonstration of recommendation system
"""

# -- utf8-console-guard --
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


import json
from pathlib import Path

# Import system modules
from src.parsing import ResumeParser, JDParser
from src.recommendation import RecommendationEngine, ExplainabilityEngine, RankingEngine
from src.evaluation import Evaluator
from src.recommendation.guardrail import GuardrailValidator


def load_sample_data():
    """Load sample student and job data."""
    data_path = Path('data/raw')
    
    with open(data_path / 'sample_students.json') as f:
        students = json.load(f)
    
    with open(data_path / 'sample_jobs.json') as f:
        jobs = json.load(f)
    
    return students, jobs


def main():
    """Run complete demo."""
    print("=" * 80)
    print("AI PLACEMENT RECOMMENDATION SYSTEM - LIVE DEMO")
    print("=" * 80)
    print()
    
    # Load data
    print("STEP 1: Loading Student & Job Data")
    print("-" * 80)
    students, jobs = load_sample_data()
    print(f"✓ Loaded {len(students)} students")
    print(f"✓ Loaded {len(jobs)} jobs")
    print()
    
    # Initialize engines
    print("STEP 2: Initializing Recommendation Engine")
    print("-" * 80)
    recommendation_engine = RecommendationEngine()
    recommendation_engine.load_students(students)
    recommendation_engine.load_jobs(jobs)
    explainability_engine = ExplainabilityEngine()
    ranking_engine = RankingEngine()
    print("✓ Recommendation engine initialized")
    print()
    
    # Select a student for demo
    demo_student_id = 1
    demo_student = next(s for s in students if s['student_id'] == demo_student_id)
    
    print("STEP 3: Selecting Demo Student")
    print("-" * 80)
    print(f"Student ID: {demo_student_id}")
    print(f"Name: {demo_student['name']}")
    print(f"Verified Skills: {', '.join(demo_student['verified_skills'])}")
    print(f"Years of Experience: {demo_student['years_experience']}")
    print(f"Assessment Score: {demo_student['assessment_score']:.2%}")
    print(f"Education: {demo_student['education']}")
    print(f"Certifications: {', '.join(demo_student['certifications']) or 'None'}")
    print()
    
    # Generate recommendations
    print("STEP 4: Generating Recommendations")
    print("-" * 80)
    recommendations = recommendation_engine.recommend(demo_student_id, top_k=5)
    ranked = ranking_engine.rank_recommendations(recommendations, method='score')
    
    for rec in ranked:
        print(f"Rank {rec['rank']}: {rec['title']} @ {rec['company']} - Score: {rec['score']:.1%}")
    print()
    
    # Show detailed explanation for top recommendation
    if ranked:
        top_job_id = ranked[0]['job_id']
        top_job = next(j for j in jobs if j['job_id'] == top_job_id)
        
        print("STEP 5: Detailed Explanation for Top Recommendation")
        print("-" * 80)
        print(f"Job: {top_job['title']} @ {top_job['company']}")
        print()
        
        # Extract features
        from src.recommendation.feature_engineering import FeatureEngineer
        feature_engineer = FeatureEngineer()
        features = feature_engineer.extract_features(demo_student, top_job)
        score = feature_engineer.compute_score(features)
        
        # Get explanation
        explanation = explainability_engine.explain_recommendation(
            demo_student, top_job, features, score
        )
        
        print(explainability_engine.format_explanation(explanation))
        print()
    
    # Run full evaluation
    print("STEP 6: System Evaluation")
    print("-" * 80)
    evaluator = Evaluator()
    evaluation_results = evaluator.evaluate_system(students, jobs)
    
    print(evaluator.generate_summary_report())
    print()
    
    # Data quality checks
    print("STEP 7: Data Quality & Guardrails")
    print("-" * 80)
    guardrail_validator = GuardrailValidator()
    quality_report = guardrail_validator.get_quality_report(students, jobs)
    
    print(f"Students with Skills: {quality_report['students']['with_skills']}/{quality_report['students']['count']}")
    print(f"Students with Assessment Scores: {quality_report['students']['with_assessment']}/{quality_report['students']['count']}")
    print(f"Avg Skills per Student: {quality_report['students']['avg_skills']:.1f}")
    print()
    print(f"Jobs with Requirements: {quality_report['jobs']['with_requirements']}/{quality_report['jobs']['count']}")
    print(f"Avg Required Skills per Job: {quality_report['jobs']['avg_required_skills']:.1f}")
    print()
    
    # Save results
    print("STEP 8: Saving Results")
    print("-" * 80)
    
    # Save recommendations
    demo_results = {
        'student_id': demo_student_id,
        'student_name': demo_student['name'],
        'recommendations': [
            {
                'rank': rec['rank'],
                'job_id': rec['job_id'],
                'title': rec['title'],
                'company': rec['company'],
                'score': rec['score']
            }
            for rec in ranked
        ],
        'evaluation_date': '2024-01-15'
    }
    
    with open('reports/demo_examples.json', 'w') as f:
        json.dump(demo_results, f, indent=2)
    
    # Save evaluation results
    evaluator.save_report('reports/evaluation_results.json')
    
    print("✓ Results saved to reports/")
    print()
    
    print("=" * 80)
    print("DEMO COMPLETE")
    print("=" * 80)
    print()
    print("Next Steps:")
    print("1. Start API: uvicorn src.api.app:app --reload")
    print("2. Test endpoint: curl http://localhost:8000/api/recommend -d '{\"student_id\": 1}'")
    print("3. View metrics: curl http://localhost:8000/api/metrics")
    print()


if __name__ == '__main__':
    main()
