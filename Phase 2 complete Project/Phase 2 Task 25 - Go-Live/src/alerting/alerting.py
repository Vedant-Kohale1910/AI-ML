"""Alerting System - Task 25"""
from typing import Dict, List, Any

class AlertSystem:
    """Manage alerts and anomalies in production."""
    
    def __init__(self):
        """Initialize alert system."""
        self.rules = {}
        self.alerts = []
    
    def add_rule(self, name: str, metric: str, 
                threshold: float, operator: str = '<') -> None:
        """Add alert rule."""
        self.rules[name] = {
            'metric': metric,
            'threshold': threshold,
            'operator': operator
        }
    
    def check_metrics(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        """Check metrics against rules."""
        triggered_alerts = []
        
        for rule_name, rule in self.rules.items():
            metric_value = metrics.get(rule['metric'], 0)
            threshold = rule['threshold']
            
            triggered = False
            if rule['operator'] == '<' and metric_value < threshold:
                triggered = True
            elif rule['operator'] == '>' and metric_value > threshold:
                triggered = True
            
            if triggered:
                alert = {
                    'rule': rule_name,
                    'metric': rule['metric'],
                    'value': metric_value,
                    'threshold': threshold,
                    'severity': 'WARNING' if metric_value > threshold * 0.9 else 'CRITICAL'
                }
                triggered_alerts.append(alert)
                self.alerts.append(alert)
        
        return triggered_alerts
    
    def get_alert_history(self) -> List[Dict[str, Any]]:
        """Get alert history."""
        return self.alerts
