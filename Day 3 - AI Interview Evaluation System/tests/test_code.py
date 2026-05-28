from code_analyzer import CodeAnalyzer

sample_code = """
def add(a, b):
    return a + b
"""
analyzer = CodeAnalyzer(sample_code)
print(analyzer.analyze())
