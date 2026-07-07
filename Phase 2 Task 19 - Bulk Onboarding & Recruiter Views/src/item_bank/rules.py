"""
Item Quality Rules - Task 19
Configurable thresholds and rules
"""

# Difficulty thresholds
DIFFICULTY_THRESHOLDS = {
    'too_easy': 0.95,              # > 95% correct → too easy
    'too_difficult': 0.20,          # < 20% correct → too difficult
    'too_difficult_critical': 0.10  # < 10% correct → critically difficult
}

# Discrimination thresholds
DISCRIMINATION_THRESHOLDS = {
    'good': 0.30,
    'fair': 0.20,
    'poor': 0.10
}

# Risk level definitions
RISK_LEVELS = {
    'RED': {
        'description': 'Critical - needs immediate review/replacement',
        'priority': 1,
        'action': 'REPLACE'
    },
    'YELLOW': {
        'description': 'Review - needs improvement or replacement',
        'priority': 2,
        'action': 'REVIEW'
    },
    'GREEN': {
        'description': 'Good - no action needed',
        'priority': 3,
        'action': 'NONE'
    }
}

# Issue type definitions
ISSUE_TYPES = {
    'TOO_EASY': 'Question answered correctly by >95% of students',
    'TOO_DIFFICULT': 'Question answered correctly by <20% of students',
    'LOW_DISCRIMINATION': 'Question has poor discrimination index',
    'GOOD': 'Question performs well'
}


def get_default_rules():
    """Get default detection rules."""
    return {
        'too_easy_threshold': DIFFICULTY_THRESHOLDS['too_easy'],
        'too_difficult_threshold': DIFFICULTY_THRESHOLDS['too_difficult'],
        'poor_discrimination_threshold': DISCRIMINATION_THRESHOLDS['poor'],
        'min_attempts_required': 10,
        'time_threshold_seconds': 300  # 5 minutes
    }


def get_rule_config():
    """Get complete rule configuration."""
    return {
        'difficulty_thresholds': DIFFICULTY_THRESHOLDS,
        'discrimination_thresholds': DISCRIMINATION_THRESHOLDS,
        'risk_levels': RISK_LEVELS,
        'issue_types': ISSUE_TYPES,
        'default_rules': get_default_rules()
    }
