import ast
from radon.complexity import cc_visit

class CodeAnalyzer:
    def __init__(self, code):
        self.code = code

    def complexity_score(self):
        try:
            complexity = cc_visit(self.code)
            avg_complexity = sum(c.complexity for c in complexity) / len(complexity)

            score = max(0, 100 - avg_complexity * 5)
            return round(score, 2)
        except:
            return 40

    def style_score(self):
        penalties = 0
        if "def " not in self.code:
            penalties += 20

        if "#" not in self.code:
            penalties += 10

        if len(self.code.splitlines()) > 50:
            penalties += 10

        return max(0, 100 - penalties)

    def correctness_score(self):
        try:
            ast.parse(self.code)
            return 90
        except:
            return 30

    def analyze(self):
        correctness = self.correctness_score()
        complexity = self.complexity_score()
        style = self.style_score()
        final_score = (
            0.5 * correctness +
            0.3 * complexity +
            0.2 * style
        )
        return {
            "correctness_score": correctness,
            "complexity_score": complexity,
            "style_score": style,
            "problem_solving_score": round(final_score, 2)
        }