"""Metrics Monitoring Module - Task 22"""
from typing import Dict, List, Any

class MetricsMonitor:
    """Monitor recommendation metrics."""
    
    def calculate_precision(self, tp: int, fp: int) -> float:
        """Calculate precision."""
        if tp + fp == 0:
            return 0.0
        return tp / (tp + fp)
    
    def calculate_recall(self, tp: int, fn: int) -> float:
        """Calculate recall."""
        if tp + fn == 0:
            return 0.0
        return tp / (tp + fn)
    
    def calculate_fpr(self, fp: int, tn: int) -> float:
        """Calculate false positive rate."""
        if fp + tn == 0:
            return 0.0
        return fp / (fp + tn)
    
    def get_current_metrics(self, baseline_metrics: Dict[str, float],
                           current_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Compare current metrics with baseline."""
        return {
            'baseline': baseline_metrics,
            'current': current_metrics,
            'changes': {
                'precision': current_metrics.get('precision', 0) - 
                           baseline_metrics.get('precision', 0),
                'recall': current_metrics.get('recall', 0) - 
                        baseline_metrics.get('recall', 0),
                'fpr': current_metrics.get('fpr', 0) - 
                     baseline_metrics.get('fpr', 0)
            }
        }
