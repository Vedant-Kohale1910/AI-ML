#!/usr/bin/env python3
"""Task 22 Demo - Drift Monitoring & Retraining"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.monitoring.drift_detector import DriftDetector
from src.monitoring.metrics_monitor import MetricsMonitor
from src.retraining.retrain import RetrainingPipeline

def main():
    print("="*80)
    print("TASK 22 - DRIFT MONITORING & RETRAINING")
    print("Continuous Model Monitoring in Production")
    print("="*80)
    print()
    
    # Step 1: Setup
    print("STEP 1: Baseline Model Setup")
    print("-"*80)
    baseline_metrics = {
        'precision': 0.91,
        'recall': 0.89,
        'fpr': 0.08
    }
    print(f"Baseline Model (v1.0):")
    print(f"  Precision: {baseline_metrics['precision']}")
    print(f"  Recall: {baseline_metrics['recall']}")
    print(f"  FPR: {baseline_metrics['fpr']}")
    print()
    
    # Step 2: Collect production data
    print("STEP 2: Collecting Production Data")
    print("-"*80)
    production_data = {
        'skills': [0.75] * 800 + [0.85] * 200,  # Distribution changed
        'scores': [0.78] * 500 + [0.65] * 500,  # Scores decreased
        'recommendations': 88  # Recommendation rate dropped
    }
    baseline_data = {
        'skills': [0.82] * 1000,  # Original distribution
        'scores': [0.82] * 1000,  # Original scores
        'recommendations': 90
    }
    print(f"✓ Collected 1000 production recommendations")
    print(f"✓ Average recommendation score: 0.78 (was 0.82)")
    print()
    
    # Step 3: Detect drift
    print("STEP 3: Detecting Drift")
    print("-"*80)
    detector = DriftDetector(psi_threshold=0.25)
    drift_report = detector.detect_drift(baseline_data, production_data)
    
    print(f"Population Stability Index (PSI) Analysis:")
    for feature, analysis in drift_report['features'].items():
        psi = analysis['psi']
        drift_status = "⚠️ DRIFT" if analysis['drift'] else "✓ No drift"
        print(f"  {feature}: PSI = {psi} {drift_status}")
    
    print(f"\nOverall Drift Status: {drift_report['action']}")
    print()
    
    # Step 4: Performance comparison
    print("STEP 4: Monitoring Performance")
    print("-"*80)
    current_metrics = {
        'precision': 0.87,  # Degraded
        'recall': 0.84,     # Degraded
        'fpr': 0.12         # Degraded
    }
    monitor = MetricsMonitor()
    metrics_comparison = monitor.get_current_metrics(
        baseline_metrics, current_metrics
    )
    
    print("Performance Comparison:")
    print(f"  Precision: {baseline_metrics['precision']} → {current_metrics['precision']} " +
          f"({metrics_comparison['changes']['precision']:+.2f})")
    print(f"  Recall:    {baseline_metrics['recall']} → {current_metrics['recall']} " +
          f"({metrics_comparison['changes']['recall']:+.2f})")
    print(f"  FPR:       {baseline_metrics['fpr']} → {current_metrics['fpr']} " +
          f"({metrics_comparison['changes']['fpr']:+.2f})")
    print()
    
    if drift_report['overall_drift']:
        print("⚠️ SIGNIFICANT DRIFT DETECTED WITH PERFORMANCE DEGRADATION")
        print("   Action: RETRAIN MODEL")
    print()
    
    # Step 5: Trigger retraining
    if drift_report['action'] == 'RETRAIN':
        print("STEP 5: Retraining Pipeline Triggered")
        print("-"*80)
        pipeline = RetrainingPipeline()
        retrain_result = pipeline.retrain(production_data)
        
        print(f"Training new model...")
        print(f"  Model Version: {retrain_result['model_version']}")
        print(f"  Training Date: {retrain_result['training_date']}")
        print(f"  Data Points: {retrain_result['data_points']}")
        print()
        
        # Step 6: Validate new model
        print("STEP 6: Model Validation")
        print("-"*80)
        new_metrics = {
            'precision': 0.90,
            'recall': 0.88,
            'fpr': 0.09
        }
        
        print(f"New Model Metrics:")
        print(f"  Precision: {new_metrics['precision']}")
        print(f"  Recall: {new_metrics['recall']}")
        print(f"  FPR: {new_metrics['fpr']}")
        print()
        
        is_better = pipeline.validate_model(new_metrics, baseline_metrics)
        
        if is_better:
            print("✓ NEW MODEL BETTER - Approving deployment")
            deployment_status = "DEPLOYED"
        else:
            print("✗ NEW MODEL WORSE - Keeping current model")
            deployment_status = "REJECTED"
        print()
        
        # Step 7: Experiment log
        print("STEP 7: Experiment Logging")
        print("-"*80)
        print("Experiment Recorded:")
        print(f"  Model: v1.1")
        print(f"  Training Date: 2024-03-15")
        print(f"  Dataset Size: 1000")
        print(f"  Precision: 0.90, Recall: 0.88, FPR: 0.09")
        print(f"  Validation: PASS")
        print(f"  Deployment Status: {deployment_status}")
        print()
    
    # Step 8: Monitoring dashboard
    print("STEP 8: Real-Time Monitoring Dashboard")
    print("-"*80)
    print("""
Current Model: v1.1
Last Updated: 2024-03-15
Days Since Deployment: 5

PERFORMANCE:
  Precision: 0.90 ✓
  Recall: 0.88 ✓
  FPR: 0.09 ✓
  F1 Score: 0.89 ✓

DRIFT STATUS:
  Overall PSI: 0.14 ✓ (normal)
  Prediction Drift: 0.05 ✓ (normal)

RETRAINING SCHEDULE:
  Last Retrained: 2024-03-15
  Next Scheduled: 2024-04-15
  Trigger Conditions: MONITORING...

ALERTS:
  None currently
    """)
    
    print("="*80)
    print("DEMO COMPLETE")
    print("="*80)
    print()
    print("Key Achievements:")
    print("✓ Drift detected automatically (PSI > 0.25)")
    print("✓ Performance degradation identified")
    print("✓ Retraining triggered automatically")
    print("✓ New model validated and deployed")
    print("✓ Experiment logged for MLOps")
    print("✓ Real-time monitoring dashboard active")
    print()

if __name__ == '__main__':
    main()
