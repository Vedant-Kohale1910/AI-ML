"""Model Registry - Task 23"""
from typing import Dict, List, Any
from datetime import datetime

class ModelRegistry:
    """Manage model versions and deployments."""
    
    def __init__(self):
        """Initialize model registry."""
        self.models = {}
        self.deployment_history = []
    
    def register_model(self, name: str, version: str, 
                      metrics: Dict[str, float],
                      dataset_size: int,
                      parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new model version."""
        model_id = f"{name}_{version}"
        model_info = {
            'name': name,
            'version': version,
            'created': datetime.now().isoformat(),
            'metrics': metrics,
            'dataset_size': dataset_size,
            'parameters': parameters,
            'status': 'STAGED'
        }
        self.models[model_id] = model_info
        return model_info
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List all registered models."""
        return list(self.models.values())
    
    def get_model(self, model_id: str) -> Dict[str, Any]:
        """Get specific model info."""
        return self.models.get(model_id)
    
    def promote_to_production(self, model_id: str) -> bool:
        """Promote model to production."""
        if model_id in self.models:
            self.models[model_id]['status'] = 'CURRENT'
            self.deployment_history.append({
                'model_id': model_id,
                'timestamp': datetime.now().isoformat(),
                'action': 'promoted_to_production'
            })
            return True
        return False
    
    def rollback_to_version(self, model_id: str) -> bool:
        """Rollback to previous version."""
        if model_id in self.models:
            self.deployment_history.append({
                'model_id': model_id,
                'timestamp': datetime.now().isoformat(),
                'action': 'rollback'
            })
            return True
        return False
    
    def get_deployment_history(self) -> List[Dict[str, Any]]:
        """Get deployment history."""
        return self.deployment_history
