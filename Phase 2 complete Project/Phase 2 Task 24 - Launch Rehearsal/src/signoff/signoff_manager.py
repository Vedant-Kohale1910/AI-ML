"""Sign-Off Manager - Task 24"""
from typing import Dict, Any
from datetime import datetime

class SignoffManager:
    """Manage stakeholder sign-offs."""
    
    def __init__(self):
        """Initialize signoff manager."""
        self.approvals = {}
    
    def add_approval(self, stakeholder: str, status: str, date: str = None) -> Dict[str, Any]:
        """Record stakeholder approval."""
        if date is None:
            date = datetime.now().isoformat()[:10]
        
        approval = {
            'stakeholder': stakeholder,
            'status': status,
            'date': date,
            'timestamp': datetime.now().isoformat()
        }
        self.approvals[stakeholder] = approval
        return approval
    
    def get_all_approvals(self) -> Dict[str, Any]:
        """Get all approvals."""
        all_approved = all(a.get('status') == 'APPROVED' for a in self.approvals.values())
        return {
            'total_stakeholders': len(self.approvals),
            'approvals': self.approvals,
            'all_approved': all_approved,
            'approval_status': 'COMPLETE' if all_approved else 'PENDING'
        }
