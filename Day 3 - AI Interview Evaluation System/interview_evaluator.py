from speech_analyzer import SpeechAnalyzer
from code_analyzer import CodeAnalyzer
from feedback_generator import FeedbackGenerator

class InterviewEvaluator:
    def __init__(self, transcript, code, time_taken):
        self.transcript = transcript
        self.code = code
        self.time_taken = time_taken

    def time_management_score(self):
        if self.time_taken < 20:
            return 100
        elif self.time_taken < 30:
            return 80
        elif self.time_taken < 45:
            return 60
        else:
            return 40

    def evaluate(self):
        speech_results = SpeechAnalyzer(
            self.transcript
        ).analyze()

        code_results = CodeAnalyzer(
            self.code
        ).analyze()

        time_score = self.time_management_score()
        final_score = (
            0.4 * speech_results["communication_score"] +
            0.4 * code_results["problem_solving_score"] +
            0.2 * time_score
        )

        results = {
            **speech_results,
            **code_results,
            "time_management_score": time_score,
            "final_score": round(final_score, 2)
        }

        feedback = FeedbackGenerator.generate(results)
        results["feedback"] = feedback

        return results

if __name__ == "__main__":
    transcript = """
    I used binary search because it reduces time complexity.
    The approach is efficient and scalable.
    """

    code = """
def binary_search(arr, target):
    low = 0
    high = len(arr) - 1

    while low <= high:
        mid = (low + high) // 2

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1

    return -1
"""

    evaluator = InterviewEvaluator(transcript, code,25)

    print(evaluator.evaluate())