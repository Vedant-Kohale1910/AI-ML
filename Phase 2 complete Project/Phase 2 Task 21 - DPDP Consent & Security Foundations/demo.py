#!/usr/bin/env python3
"""Task 21 Demo - Fairness Audit"""

# -- utf8-console-guard --
import sys as _sys
try:
    _sys.stdout.reconfigure(encoding="utf-8")
    _sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.audit.fairness_audit import FairnessAudit
from src.metrics.fairness_metrics import FairnessMetrics
from src.bias_detection.bias_detector import BiasDetector
from src.reporting.audit_reporter import AuditReporter

def generate_sample_data():
    """Generate sample recommendation data with bias."""
    recommendations = []
    # Male students
    for i in range(527):
        recommendations.append({
            'student_id': i,
            'gender': 'Male',
            'caste': 'General' if i < 350 else 'OBC',
            'score': 0.75 + (i % 10) * 0.02,
            'recommended': 0.99 if i < 520 else 0.50
        })
    
    # Female students
    for i in range(473):
        recommendations.append({
            'student_id': 527 + i,
            'gender': 'Female',
            'caste': 'General' if i < 200 else 'OBC',
            'score': 0.68 + (i % 10) * 0.02,
            'recommended': 0.85 if i < 401 else 0.30
        })
    
    # SC/ST students
    for i in range(300):
        recommendations.append({
            'student_id': 1000 + i,
            'gender': 'Male' if i < 150 else 'Female',
            'caste': 'SC/ST',
            'score': 0.62 + (i % 10) * 0.02,
            'recommended': 0.50 if i < 152 else 0.40
        })
    
    return recommendations

def main():
    print("="*80)
    print("TASK 21 - FAIRNESS AUDIT")
    print("Bias Detection in Recommendation System")
    print("="*80)
    print()
    
    # Step 1: Generate data
    print("STEP 1: Generating Sample Recommendation Data")
    print("-"*80)
    recommendations = generate_sample_data()
    print(f"✓ Generated {len(recommendations)} recommendations")
    print(f"✓ Data includes demographic attributes (gender, caste)")
    print()
    
    # Step 2: Audit by group
    print("STEP 2: Auditing Recommendations by Demographic Group")
    print("-"*80)
    audit = FairnessAudit()
    
    # Gender audit
    print("\nAuditing by GENDER:")
    gender_audit = audit.audit_by_group(recommendations, 'gender')
    for group, metrics in gender_audit['groups'].items():
        print(f"  {group}: {metrics['recommendation_rate']*100:.1f}% recommendation rate")
    
    gender_bias = audit.detect_bias(
        gender_audit['disparities']['disparate_impact'],
        gender_audit['disparities']['disparity_percentage']
    )
    print(f"  Disparate Impact: {gender_bias['disparate_impact']:.3f}")
    print(f"  Bias Level: {gender_bias['bias_level']}")
    print()
    
    # Caste audit
    print("Auditing by CASTE:")
    caste_audit = audit.audit_by_group(recommendations, 'caste')
    for group, metrics in caste_audit['groups'].items():
        print(f"  {group}: {metrics['recommendation_rate']*100:.1f}% recommendation rate")
    
    caste_bias = audit.detect_bias(
        caste_audit['disparities']['disparate_impact'],
        caste_audit['disparities']['disparity_percentage']
    )
    print(f"  Disparate Impact: {caste_bias['disparate_impact']:.3f}")
    print(f"  Bias Level: {caste_bias['bias_level']}")
    print()
    
    # Step 3: Generate report
    print("STEP 3: Generating Fairness Audit Report")
    print("-"*80)
    reporter = AuditReporter()
    report = reporter.generate_audit_report(
        {'gender': gender_audit, 'caste': caste_audit},
        {'gender': gender_bias, 'caste': caste_bias}
    )
    print(report)
    
    # Step 4: Recommendations
    print("STEP 4: Mitigation Strategies")
    print("-"*80)
    if gender_bias['requires_action']:
        print(f"Gender Bias: {gender_bias['bias_level']}")
        print(f"  → Review assessment scoring for gender bias")
        print(f"  → Adjust recommendation thresholds if needed")
    
    if caste_bias['requires_action']:
        print(f"Caste Bias: {caste_bias['bias_level']}")
        print(f"  → Review for systemic disadvantages")
        print(f"  → Ensure equal opportunity in skill development")
        print(f"  → Monitor recommendations closely")
    
    print()
    print("="*80)
    print("DEMO COMPLETE")
    print("="*80)

if __name__ == '__main__':
    main()
