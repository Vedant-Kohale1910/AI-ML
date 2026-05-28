class FeedbackGenerator:
    @staticmethod
    def generate(results):
        feedback = []
        if results["communication_score"] < 60:
            feedback.append(
                "Improve communication clarity and confidence."
            )

        if results["problem_solving_score"] < 60:
            feedback.append(
                "Practice algorithm optimization and clean coding."
            )

        if results["time_management_score"] < 60:
            feedback.append(
                "Improve time management during interviews."
            )

        if not feedback:
            feedback.append(
                "Excellent overall interview performance."
            )
        return feedback
