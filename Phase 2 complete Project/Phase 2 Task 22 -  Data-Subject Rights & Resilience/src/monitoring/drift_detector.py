"""Drift Detection Module - Task 22"""
from typing import Dict, List, Any
import numpy as np

class DriftDetector:
    """Detect data and concept drift."""
    
    def __init__(self, psi_threshold: float = 0.25):
        """Initialize drift detector."""
        self.psi_threshold = psi_threshold
    
    def calculate_psi(self, baseline: List[float], 
                     production: List[float]) -> float:
        """Calculate Population Stability Index."""
        if len(baseline) == 0 or len(production) == 0:
            return 0.0
        
        # Binning
        bins = np.histogram_bin_edges(baseline + production, bins=10)
        baseline_counts = np.histogram(baseline, bins=bins)[0]
        production_counts = np.histogram(production, bins=bins)[0]
        
        # Normalize
        baseline_pct = baseline_counts / len(baseline)
        production_pct = production_counts / len(production)
        
        # Calculate PSI
        psi = 0
        for b, p in zip(baseline_pct, production_pct):
            if b > 0 and p > 0:
                psi += (p - b) * np.log(p / b)
        
        return round(psi, 4)
    
    def detect_drift(self, baseline_data: Dict[str, Any],
                    production_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect drift between baseline and production."""
        drift_results = {
            'overall_drift': False,
            'features': {},
            'recommendations': {}
        }
        
        # Check skill distribution drift
        if 'skills' in baseline_data and 'skills' in production_data:
            psi = self.calculate_psi(
                baseline_data['skills'],
                production_data['skills']
            )
            drift_results['features']['skills'] = {
                'psi': psi,
                'drift': psi > self.psi_threshold
            }
        
        # Check recommendation score drift
        if 'scores' in baseline_data and 'scores' in production_data:
            psi = self.calculate_psi(
                baseline_data['scores'],
                production_data['scores']
            )
            drift_results['features']['scores'] = {
                'psi': psi,
                'drift': psi > self.psi_threshold
            }
        
        # Overall drift
        drift_results['overall_drift'] = any(
            f.get('drift', False) for f in drift_results['features'].values()
        )
        
        if drift_results['overall_drift']:
            drift_results['action'] = 'RETRAIN'
        else:
            drift_results['action'] = 'MONITOR'
        
        return drift_results
