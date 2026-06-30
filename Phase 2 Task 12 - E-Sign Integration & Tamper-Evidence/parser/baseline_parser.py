"""
baseline_parser.py

The naive first pass at parsing - exactly what you'd write if someone
said "just check whether each skill name shows up in the text" without
thinking too hard about it. Two things wrong with it, both on purpose:

1. Plain substring search, no word boundaries - "Java" matches inside
   "JavaScript", so any resume that only knows JavaScript gets credited
   with Java too.
2. No context awareness - "currently learning Kubernetes" mentions
   Kubernetes, so this counts it as a skill the candidate has, even
   though the sentence says the opposite.

Both of these are realistic mistakes, not strawmen - "does the string
appear in the document" is usually the first thing anyone tries.
"""

from skills_ontology import CANONICAL_SKILLS


def baseline_extract_skills(text: str):
    text_lower = text.lower()
    found = []
    for skill in CANONICAL_SKILLS:
        if skill.lower() in text_lower:
            found.append(skill)
    return sorted(set(found))
