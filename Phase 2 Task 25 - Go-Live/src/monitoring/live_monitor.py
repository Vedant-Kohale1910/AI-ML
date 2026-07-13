"""Live Model Monitoring - Task 25"""
from typing import Dict, List, Any
from datetime import datetime

class LiveMonitor:
    """Monitor model performance live in production."""
    
    def __init__(self):
        """Initialize live monitor."""
        self.predictions = []
        self.metrics_cache = {}
    
    def record_prediction(self, student_id: int, job_id: int,
                         predicted_score: float,
                         actual_hired: bool = None) -> Dict[str, Any]:
        """Record a prediction for monitoring."""
        prediction = {
            'timestamp': datetime.now().isoformat(),
            'student_id': student_id,
            'job_id': job_id,
            'predicted_score': predicted_score,
            'actual_hired': actual_hired,
            'recommendation': predicted_score >= 0.70
        }
        self.predictions.append(prediction)
        return prediction
    
    def get_metrics(self, window: str = '24h') -> Dict[str, float]:
        """Calculate current metrics."""
        if not self.predictions:
            return {'precision': 0.0, 'recall': 0.0, 'fpr': 0.0}
        
        # Simulate metrics calculation
        tp = sum(1 for p in self.predictions 
                if p['recommendation'] and p['actual_hired'])
        fp = sum(1 for p in self.predictions 
                if p['recommendation'] and not p['actual_hired'])
        fn = sum(1 for p in self.predictions 
                if not p['recommendation'] and p['actual_hired'])
        tn = sum(1 for p in self.predictions 
                if not p['recommendation'] and not p['actual_hired'])
        
        total = tp + fp + fn + tn
        if total == 0:
            return {'precision': 0.0, 'recall': 0.0, 'fpr': 0.0}
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        
        return {
            'precision': round(precision, 4),
            'recall': round(recall, 4),
            'fpr': round(fpr, 4),
            'predictions': len(self.predictions),
            'window': window
        }
    
    def get_throughput(self) -> Dict[str, Any]:
        """Get system throughput."""
        return {
            'total_predictions': len(self.predictions),
            'predictions_per_hour': len(self.predictions),
            'successful': len([p for p in self.predictions if p is not None]),
            'failed': 0
        }
