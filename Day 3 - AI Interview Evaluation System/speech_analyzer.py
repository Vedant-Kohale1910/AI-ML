from textblob import TextBlob
import language_tool_python
import re

tool = language_tool_python.LanguageTool('en-US')

class SpeechAnalyzer:
    def __init__(self, transcript):
        self.transcript = transcript

    def grammar_score(self):
        matches = tool.check(self.transcript)
        error_count = len(matches)
        score = max(0, 100 - error_count * 2)
        return score

    def sentiment_score(self):
        polarity = TextBlob(self.transcript).sentiment.polarity
        score = (polarity + 1) * 50
        return round(score, 2)

    def vocabulary_score(self):
        words = re.findall(r'\w+', self.transcript.lower())
        unique_words = len(set(words))
        total_words = len(words)

        if total_words == 0:
            return 0

        ratio = unique_words / total_words
        return round(ratio * 100, 2)

    def analyze(self):

        grammar = self.grammar_score()
        sentiment = self.sentiment_score()
        vocabulary = self.vocabulary_score()

        communication_score = (
            0.4 * sentiment +
            0.3 * grammar +
            0.3 * vocabulary
        )

        return {
            "grammar_score": grammar,
            "sentiment_score": sentiment,
            "vocabulary_score": vocabulary,
            "communication_score": round(communication_score, 2)
        }
