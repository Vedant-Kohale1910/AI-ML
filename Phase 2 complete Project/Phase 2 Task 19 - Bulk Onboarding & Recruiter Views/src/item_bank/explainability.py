"""
Item-Bank Explainability - Task 19
Generate plain-English explanations for item quality issues
"""

from typing import Dict, Any


class ItemQualityExplainer:
    """Generate explanations for item quality assessments."""
    
    def explain_item_quality(self, item_analysis: Dict[str, Any]) -> Dict[str, str]:
        """
        Generate comprehensive explanation for an item.
        
        Args:
            item_analysis: Classification result from detector
            
        Returns:
            Dictionary with various explanation formats
        """
        if item_analysis['status'] == 'GOOD':
            return self._explain_good_item(item_analysis)
        else:
            return self._explain_weak_item(item_analysis)
    
    def _explain_good_item(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate explanation for good items."""
        return {
            'summary': f"Question {analysis['question_id']} is performing well.",
            'detailed': f"""
QUESTION {analysis['question_id']}: GOOD QUESTION (GREEN)

Performance:
- Correct Rate: {analysis['correct_percentage']}%
- Attempts: {analysis['total_attempts']}
- Discrimination Index: {analysis['discrimination_index']}

Assessment:
This question effectively distinguishes between stronger and weaker students. 
The correct rate of {analysis['correct_percentage']}% indicates appropriate difficulty,
and students with varied abilities answer differently.

Recommendation:
✓ Keep this question. It is working well in the assessment.
""",
            'short': f"{analysis['question_id']}: Good - keep as is",
            'action': "NONE"
        }
    
    def _explain_weak_item(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Generate explanation for weak items."""
        issue = analysis['issue_type']
        
        if issue == 'TOO_EASY':
            return self._explain_too_easy(analysis)
        elif issue == 'TOO_DIFFICULT':
            return self._explain_too_difficult(analysis)
        elif issue == 'LOW_DISCRIMINATION':
            return self._explain_low_discrimination(analysis)
        
        return {}
    
    def _explain_too_easy(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Explanation for too-easy questions."""
        return {
            'summary': f"Question {analysis['question_id']} is too easy ({analysis['correct_percentage']}% correct)",
            'detailed': f"""
QUESTION {analysis['question_id']}: TOO EASY (RED - CRITICAL)

Performance:
- Correct Rate: {analysis['correct_percentage']}% (> 95% threshold)
- Incorrect Rate: {100 - analysis['correct_percentage']}%
- Attempts: {analysis['total_attempts']}
- Discrimination Index: {analysis['discrimination_index']} (low)

Problem:
{analysis['correct_percentage']}% of students answered this question correctly. This is too high.
The question fails to differentiate between students who deeply understand
the material and those who guessed correctly or have superficial knowledge.

Why It Matters:
- Cannot identify weak students: Everyone passes it
- Skews overall assessment: Inflates scores artificially
- Wastes test time: Doesn't provide useful information
- Biases results: May favor students who guess well

Root Cause Analysis:
1. Question wording may be too clear/leading
2. Options may be too obviously wrong
3. Concept being tested may be too basic
4. Students may have prior knowledge beyond what was taught

Recommended Actions:
🔴 CRITICAL - This question should be reviewed and likely replaced

Actions to Take:
1. IMMEDIATE: Consider removing from assessment temporarily
2. Review: Check student feedback about this question
3. Analysis: Examine answer distribution (all students chose same option?)
4. Revision Options:
   a) Make options more similar/plausible
   b) Increase question complexity
   c) Test a more advanced concept
   d) Replace with different question entirely
5. Validation: After changes, re-test with sample students

Expected Impact:
- Improving discrimination: Better separation of abilities
- Realistic scoring: Scores better reflect knowledge
- Better assessment: Identifies actual weak areas
""",
            'short': f"{analysis['question_id']}: TOO EASY - Replace or significantly revise",
            'action': "REPLACE",
            'confidence': analysis['confidence']
        }
    
    def _explain_too_difficult(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Explanation for too-difficult questions."""
        return {
            'summary': f"Question {analysis['question_id']} is too difficult ({analysis['correct_percentage']}% correct)",
            'detailed': f"""
QUESTION {analysis['question_id']}: TOO DIFFICULT (RED - CRITICAL)

Performance:
- Correct Rate: {analysis['correct_percentage']}% (< 20% threshold)
- Incorrect Rate: {100 - analysis['correct_percentage']}%
- Attempts: {analysis['total_attempts']}
- Discrimination Index: {analysis['discrimination_index']}

Problem:
Only {analysis['correct_percentage']}% of students answered this question correctly. 
This is far below the optimal range. The question is unreasonably difficult or possibly flawed.

Why It Matters:
- Demoralizes students: Everyone fails it
- Provides no discrimination: No variance in responses
- May be unfair: Tests knowledge not covered or too advanced
- Wastes assessment value: Doesn't distinguish abilities

Root Cause Analysis:
1. Concept may be too advanced for this level
2. Wording might be confusing or ambiguous
3. Requires knowledge not in curriculum
4. Question might have an error or no correct answer
5. May require multiple skills or prerequisites

Recommended Actions:
🔴 CRITICAL - This question needs immediate review

Actions to Take:
1. URGENT: Review question for errors or ambiguity
2. Verify: Confirm answer key is correct
3. Analysis: Check if students had time to answer
4. Revision Options:
   a) Simplify question wording
   b) Add hints or partial credit
   c) Break into smaller/simpler questions
   d) Teach this concept before assessment
   e) Replace with suitable alternative
5. Validation: Re-test after changes

Expected Impact:
- Better assessment validity: Tests appropriate level
- Improved student experience: Fair and reasonable
- Better discrimination: Distinguishes actual abilities
""",
            'short': f"{analysis['question_id']}: TOO DIFFICULT - Review/simplify or replace",
            'action': "REVIEW",
            'confidence': analysis['confidence']
        }
    
    def _explain_low_discrimination(self, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Explanation for low-discrimination questions."""
        return {
            'summary': f"Question {analysis['question_id']} has low discrimination index ({analysis['discrimination_index']})",
            'detailed': f"""
QUESTION {analysis['question_id']}: LOW DISCRIMINATION (YELLOW - REVIEW)

Performance:
- Correct Rate: {analysis['correct_percentage']}%
- Discrimination Index: {analysis['discrimination_index']} (< 0.20 threshold)
- Attempts: {analysis['total_attempts']}

Problem:
This question does not effectively differentiate between stronger and weaker students.
Both good and weak students answered similarly, suggesting the question doesn't
measure what it's supposed to measure or has other issues.

Why It Matters:
- Doesn't help identify weak areas: Can't tell who understands
- Reduces assessment value: Wastes test time
- May confuse rather than test: Tricks rather than assesses
- Unfair scoring: Same result regardless of ability

Root Cause Analysis:
1. May be testing unrelated concepts
2. Could have ambiguous wording
3. Might test luck/guessing rather than knowledge
4. Could require context not provided in question
5. May have multiple defensible answers

Recommended Actions:
🟡 REVIEW - Consider improving or replacing

Suggested Review Steps:
1. Analyze response patterns (do all students pick same wrong option?)
2. Check question clarity (is wording confusing?)
3. Verify relevance (does it test intended concept?)
4. Review options (are wrong options equally plausible?)
5. Consider improvements:
   a) Clarify wording
   b) Make distractors more plausible
   c) Focus on core concept
   d) Add more challenging variant
6. Test changes with sample group

Timeline: Schedule review within next assessment cycle
""",
            'short': f"{analysis['question_id']}: Low discrimination - Review and improve",
            'action': "REVIEW",
            'confidence': analysis['confidence']
        }
    
    def format_explanation_for_admin(self, analysis: Dict[str, Any]) -> str:
        """Format explanation for admin dashboard."""
        explanation = self.explain_item_quality(analysis)
        
        return f"""
{'='*70}
ITEM QUALITY ANALYSIS REPORT
{'='*70}

Question ID: {analysis['question_id']}
Status: {analysis['status']}
Risk Level: {analysis['risk_level']}
Confidence: {analysis['confidence']*100:.0f}%

PERFORMANCE METRICS:
  Correct Rate: {analysis['correct_percentage']}%
  Total Attempts: {analysis['total_attempts']}
  Difficulty: {analysis['difficulty_level']}
  Discrimination: {analysis['discrimination_index']}

SUMMARY:
{explanation['summary']}

RECOMMENDATION:
{explanation['action']}

DETAILED EXPLANATION:
{explanation['detailed']}
"""
