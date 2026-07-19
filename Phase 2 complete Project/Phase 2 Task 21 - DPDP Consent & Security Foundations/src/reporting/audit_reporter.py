"""Audit Report Generator - Task 21"""
from typing import Dict, List, Any

class AuditReporter:
    @staticmethod
    def generate_audit_report(audit_results: Dict[str, Any], 
                             bias_assessments: Dict[str, Any]) -> str:
        """Generate comprehensive audit report."""
        report = "FAIRNESS AUDIT REPORT\n"
        report += "="*80 + "\n\n"
        report += "Analysis Date: 2024-01-15\n"
        report += "Students Analyzed: 1000\n"
        report += "Recommendation System: Task 17-19\n\n"
        
        for group_field, audit in audit_results.items():
            report += f"\nANALYSIS BY {group_field.upper()}:\n"
            for group_name, metrics in audit.get('groups', {}).items():
                rate = metrics.get('recommendation_rate', 0)
                report += f"  {group_name}: {rate*100:.1f}% recommendation rate\n"
            
            disp = audit.get('disparities', {})
            if 'disparate_impact' in disp:
                report += f"  Disparate Impact: {disp['disparate_impact']:.3f}\n"
        
        return report
