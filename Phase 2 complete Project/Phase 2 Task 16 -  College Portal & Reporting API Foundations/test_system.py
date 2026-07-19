#!/usr/bin/env python
"""
Quick test script to verify Recommendation Engine v1 is working correctly
Run this to ensure all components are functional
"""

# -- utf8-console-guard --
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


import sys
from pathlib import Path
import pandas as pd

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from recommendation.recommender import RecommendationEngine
from recommendation.ranking import BaselineRecommender, MetricsEvaluator


def test_data_loading():
    """Test 1: Can we load the data?"""
    print("\n" + "="*80)
    print("TEST 1: Data Loading")
    print("="*80)
    
    try:
        data_dir = Path(__file__).parent / "data"
        students = pd.read_csv(data_dir / "students.csv")
        jobs = pd.read_csv(data_dir / "jobs.csv")
        
        print(f"✓ Loaded {len(students)} students")
        print(f"✓ Loaded {len(jobs)} jobs")
        print(f"✓ Students columns: {list(students.columns)}")
        print(f"✓ Jobs columns: {list(jobs.columns)}")
        
        return True, students, jobs
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False, None, None


def test_baseline(students, jobs):
    """Test 2: Does baseline recommender work?"""
    print("\n" + "="*80)
    print("TEST 2: Baseline Recommender (Skill Overlap)")
    print("="*80)
    
    try:
        baseline = BaselineRecommender(students, jobs)
        recommendations = baseline.recommend_jobs(student_id=1, top_n=5)
        
        print(f"✓ Generated {len(recommendations)} baseline recommendations for student 1")
        
        for rec in recommendations[:3]:
            print(f"  - {rec['job_title']:40s} Score: {rec['baseline_score']:.1%}")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        return False


def test_rec_v1(students, jobs):
    """Test 3: Does Rec v1 work?"""
    print("\n" + "="*80)
    print("TEST 3: Recommendation Engine v1 (Multi-Factor)")
    print("="*80)
    
    try:
        engine = RecommendationEngine(students, jobs)
        
        print(f"✓ Engine initialized with weights:")
        for factor, weight in engine.WEIGHTS.items():
            print(f"  - {factor:30s}: {weight:5.0%}")
        
        recommendations = engine.recommend_jobs(student_id=1, top_n=5)
        
        print(f"\n✓ Generated {len(recommendations)} Rec v1 recommendations for student 1")
        
        for rec in recommendations[:3]:
            print(f"\n  [{rec.job_title}]")
            print(f"    Overall Score: {rec.overall_score:.1%}")
            print(f"    Skill Match:  {rec.skill_match_score:.1%}")
            print(f"    Assessment:   {rec.assessment_score:.1%}")
            print(f"    Experience:   {rec.experience_match_score:.1%}")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_explanation(students, jobs):
    """Test 4: Are explanations generated?"""
    print("\n" + "="*80)
    print("TEST 4: Explainable Recommendations")
    print("="*80)
    
    try:
        engine = RecommendationEngine(students, jobs)
        report = engine.get_recommendation_report(student_id=1, top_n=3)
        
        print(f"\n✓ Generated detailed report for {report['student_name']}")
        print(f"  Skills: {report['student_profile']['skills']}")
        print(f"  Experience: {report['student_profile']['experience_years']} years")
        print(f"  Assessment: {report['student_profile']['assessment_score']}/100")
        
        for rec in report['top_recommendations'][:2]:
            print(f"\n  Job: {rec['job_title']}")
            print(f"  Score: {rec['overall_score']:.1%}")
            print(f"  Why: {rec['explanation']}")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metrics():
    """Test 5: Can we evaluate metrics?"""
    print("\n" + "="*80)
    print("TEST 5: Metrics Evaluation")
    print("="*80)
    
    try:
        evaluator = MetricsEvaluator()
        
        # Create dummy predictions
        y_true = [1, 1, 0, 1, 0, 0, 1, 1, 0, 1]
        y_pred = [1, 1, 0, 1, 0, 1, 1, 0, 0, 1]
        y_pred_proba = [0.9, 0.85, 0.1, 0.95, 0.2, 0.6, 0.88, 0.3, 0.15, 0.92]
        
        import numpy as np
        metrics = evaluator.evaluate_predictions(
            np.array(y_true),
            np.array(y_pred),
            np.array(y_pred_proba)
        )
        
        print(f"✓ Evaluated metrics on sample predictions:")
        for metric, value in metrics.items():
            if isinstance(value, float):
                print(f"  - {metric:30s}: {value:.4f}")
            else:
                print(f"  - {metric:30s}: {value}")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_students(students, jobs):
    """Test 6: Can we generate recommendations for all students?"""
    print("\n" + "="*80)
    print("TEST 6: Batch Processing (All Students)")
    print("="*80)
    
    try:
        engine = RecommendationEngine(students, jobs)
        
        results = []
        for student_id in students['student_id'].unique():
            recommendations = engine.recommend_jobs(student_id, top_n=3)
            results.append({
                'student_id': student_id,
                'recommendation_count': len(recommendations)
            })
        
        print(f"✓ Generated recommendations for {len(results)} students")
        print(f"  Sample results:")
        for result in results[:5]:
            print(f"    - Student {result['student_id']}: {result['recommendation_count']} recommendations")
        
        return True
    except Exception as e:
        print(f"✗ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("PLACEMUX RECOMMENDATION ENGINE V1 - SYSTEM TEST")
    print("="*80)
    
    results = []
    
    # Test 1: Data loading
    success, students, jobs = test_data_loading()
    results.append(("Data Loading", success))
    
    if not success:
        print("\n✗ Cannot continue without data")
        return
    
    # Test 2: Baseline
    success = test_baseline(students, jobs)
    results.append(("Baseline Recommender", success))
    
    # Test 3: Rec v1
    success = test_rec_v1(students, jobs)
    results.append(("Rec v1 Engine", success))
    
    # Test 4: Explanations
    success = test_explanation(students, jobs)
    results.append(("Explainability", success))
    
    # Test 5: Metrics
    success = test_metrics()
    results.append(("Metrics Evaluation", success))
    
    # Test 6: All students
    success = test_all_students(students, jobs)
    results.append(("Batch Processing", success))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        symbol = "✓" if success else "✗"
        print(f"{symbol} {test_name}")
    
    print(f"\nPassed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 All tests passed! Recommendation Engine v1 is ready to use.")
        print("\nNext steps:")
        print("  1. Run the Jupyter notebook: jupyter notebook notebooks/recommendation_design.ipynb")
        print("  2. Start the API: python api/app.py")
        print("  3. Visit API docs: http://localhost:8000/docs")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
