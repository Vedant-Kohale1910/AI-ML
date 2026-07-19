"""
resume_parser.py

The "v0" parser this task is actually about. Fixes both problems in
baseline_parser.py:

1. Word-boundary matching via regex, so "Java" inside "JavaScript" no
   longer counts - and skill aliases (ml -> Machine Learning, k8s ->
   Kubernetes) get normalised to one canonical name before extraction
   rather than appearing as a separate, unmatched string.

2. A small set of "aspirational/negative" cue phrases checked in the
   sentence a skill mention appears in. "Currently learning Kubernetes"
   and "no experience with AWS yet" get excluded; "5 years of experience
   in AWS" does not. This is a v0 - a handful of hand-picked phrases, not
   a trained classifier - but it's the difference between recall and
   precision that actually matters here.

Besides skills, also pulls out education (matched against a fixed
keyword list) and a rough experience-years estimate (regex for "N years"
patterns). Both are best-effort, not the main deliverable.
"""

import re

from skills_ontology import CANONICAL_SKILLS, ALIASES, EDUCATION_KEYWORDS

# phrases that, if they appear in the same sentence as a skill mention,
# mean the candidate does NOT currently have that skill. Checked as
# substrings of the lowercased sentence, deliberately simple - this is a
# v0, a real version would want a proper negation-scope classifier.
ASPIRATIONAL_CUES = [
    "currently learning", "planning to learn", "planning to pick up",
    "want to learn", "would like to learn", "would like to gain",
    "keen to learn", "interested in", "no hands-on experience",
    "no experience with", "not yet familiar", "looking to learn",
    "exploring online courses", "next role", "future role",
]

EXPERIENCE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", re.IGNORECASE)


def _build_skill_regex():
    """One compiled regex per canonical skill (and its aliases), anchored
    to word boundaries. Built once at import time rather than per-call -
    parsing a batch of resumes shouldn't recompile this every time."""
    patterns = {}
    all_names = {s: s for s in CANONICAL_SKILLS}
    for alias, canon in ALIASES.items():
        all_names[alias] = canon

    for raw_name, canon in all_names.items():
        # escape regex special chars (skills like "C++", "C#" if ever added,
        # or "." in "Vue.js"), word-boundary on both sides. \b doesn't play
        # well with a leading non-word char like "." in some skill names,
        # so we use lookaround instead of \b for safety.
        #
        # the preceding-character exclusion also rules out a "." right
        # before the match - without that, the short alias "js" would
        # happily match the tail end of "Vue.js" or "Node.js" (the
        # character right before "js" there is a dot, which otherwise
        # counts as a valid word boundary). Trailing dots are still fine
        # (end of a sentence), this only guards the left side.
        escaped = re.escape(raw_name)
        pattern = re.compile(rf"(?<![A-Za-z0-9.]){escaped}(?![A-Za-z0-9])", re.IGNORECASE)
        patterns.setdefault(canon, []).append((raw_name, pattern))
    return patterns


_SKILL_PATTERNS = _build_skill_regex()


def _split_sentences(text):
    # good enough for this dataset's template sentences - not a real NLP
    # sentence splitter, just split on sentence-ending punctuation and
    # newlines. Deliberately splits on ". " / ".\n" (period followed by
    # whitespace) rather than a bare period - splitting on every period
    # would chop "Vue.js" into "Vue" and "js", and that stray "js"
    # fragment would then match the js->JavaScript alias on its own.
    chunks = re.split(r"\.(?=\s|$)|\n", text)
    return [c.strip() for c in chunks if c.strip()]


def extract_skills(text: str, return_debug=False):
    """Returns sorted list of canonical skills found in text, after
    word-boundary matching + alias normalisation + aspirational-context
    filtering. If return_debug=True, also returns the excluded
    (aspirational) mentions, for the explainability/demo layer."""
    sentences = _split_sentences(text)
    found = set()
    excluded = []

    for canon, variants in _SKILL_PATTERNS.items():
        matched_in_sentence = False
        for sentence in sentences:
            sentence_lower = sentence.lower()
            hit = any(pattern.search(sentence) for _, pattern in variants)
            if not hit:
                continue

            is_aspirational = any(cue in sentence_lower for cue in ASPIRATIONAL_CUES)
            if is_aspirational:
                excluded.append({"skill": canon, "sentence": sentence.strip()})
            else:
                matched_in_sentence = True

        if matched_in_sentence:
            found.add(canon)

    result = sorted(found)
    if return_debug:
        return result, excluded
    return result


def extract_education(text: str):
    for kw in EDUCATION_KEYWORDS:
        # same word-boundary approach as skills - "BE" shouldn't match
        # inside an unrelated word.
        pattern = re.compile(rf"(?<![A-Za-z0-9]){re.escape(kw)}(?![A-Za-z0-9])", re.IGNORECASE)
        if pattern.search(text):
            return kw
    return None


def extract_experience_years(text: str):
    matches = EXPERIENCE_PATTERN.findall(text)
    if not matches:
        return None
    # if a resume mentions multiple "N years" phrases (it shouldn't,
    # given our templates, but real resumes might), take the largest -
    # that's usually the headline total, not a sub-project duration.
    years = [float(m) for m in matches]
    return max(years)


def parse_resume(text: str, name: str = None):
    skills, excluded = extract_skills(text, return_debug=True)
    education = extract_education(text)
    experience_years = extract_experience_years(text)

    return {
        "name": name,
        "skills": skills,
        "education": education,
        "experience_years": experience_years,
        "excluded_mentions": excluded,  # skills mentioned but not counted, with why
    }
