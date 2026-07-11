"""Feature Store - Task 23"""
from typing import Dict, List, Any

class FeatureStore:
    """Centralized feature management."""
    
    def __init__(self):
        """Initialize feature store."""
        self.features = {}
        self.feature_versions = {}
    
    def register_feature(self, name: str, version: str,
                        data_type: str, description: str,
                        depends_on: List[str] = None) -> Dict[str, Any]:
        """Register a feature."""
        feature_id = f"{name}_{version}"
        feature_info = {
            'name': name,
            'version': version,
            'data_type': data_type,
            'description': description,
            'depends_on': depends_on or [],
            'status': 'active'
        }
        self.features[feature_id] = feature_info
        
        if name not in self.feature_versions:
            self.feature_versions[name] = []
        self.feature_versions[name].append(version)
        
        return feature_info
    
    def get_feature(self, name: str, version: str = None) -> Dict[str, Any]:
        """Get feature definition."""
        if version:
            return self.features.get(f"{name}_{version}")
        else:
            # Return latest version
            if name in self.feature_versions:
                latest = self.feature_versions[name][-1]
                return self.features.get(f"{name}_{latest}")
        return None
    
    def list_features(self) -> List[Dict[str, Any]]:
        """List all features."""
        return list(self.features.values())
    
    def get_feature_lineage(self, feature_name: str) -> Dict[str, Any]:
        """Get feature dependencies."""
        feature = self.get_feature(feature_name)
        if not feature:
            return {}
        
        return {
            'feature': feature_name,
            'depends_on': feature.get('depends_on', []),
            'status': feature.get('status', 'unknown')
        }
