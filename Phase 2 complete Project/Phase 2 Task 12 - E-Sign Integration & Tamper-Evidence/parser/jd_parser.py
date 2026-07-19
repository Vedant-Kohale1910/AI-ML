"""
jd_parser.py

Job descriptions have a structure resumes don't: an explicit "Requirements"
section and, often, a separate "Nice to have" section. Lumping both into
one flat skill list (which a naive parser would do, since both sections
just contain skill names) loses real information - a matching engine
should weight a missing *required* skill very differently from a missing
*nice-to-have* one.

So this parser is section-aware: it finds the Requirements block and the
Nice-to-have block separately, and only extracts skills from within each
block's text, reusing the same word-boundary regex matching from
resume_parser.py (one canonical skill-matching implementation, not two).
"""

import re

from resume_parser import extract_skills
from skills_ontology import ROLE_TITLE_KEYWORDS

REQUIRED_HEADER_PATTERN = re.compile(r"requirements?\s*:?", re.IGNORECASE)
NICE_TO_HAVE_HEADER_PATTERN = re.compile(r"nice\s*to\s*have\s*:?", re.IGNORECASE)


def _bullet_lines_after(text: str, start_pos: int):
    """Starting right after a section header, collect consecutive bullet
    lines ('- something') until the first blank line or non-bullet line.
    This is what actually stops a trailing sentence like "We are an equal
    opportunity employer..." from leaking into the section - that line
    isn't a bullet, so collection stops before it, regardless of how far
    away the next header (or end of document) is."""
    remainder = text[start_pos:]
    lines = remainder.split("\n")
    bullets = []
    for line in lines:
        stripped = line.strip()
        if stripped == "":
            if bullets:
                break  # blank line after we've already started collecting - section is over
            continue  # blank line(s) right after the header, before the first bullet - keep looking
        if stripped.startswith("-") or stripped.startswith("*"):
            bullets.append(stripped.lstrip("-* ").strip())
        else:
            break  # first non-bullet line ends the section
    return "\n".join(bullets)


def _split_into_sections(text: str):
    """Returns (required_block, nice_to_have_block) as plain text made up
    only of the bullet lines under each header - not "everything until
    the next header or end of document", which would happily swallow
    trailing boilerplate sentences that happen to mention a skill name."""
    req_match = REQUIRED_HEADER_PATTERN.search(text)
    nice_match = NICE_TO_HAVE_HEADER_PATTERN.search(text)

    required_block = _bullet_lines_after(text, req_match.end()) if req_match else ""
    nice_block = _bullet_lines_after(text, nice_match.end()) if nice_match else ""

    return required_block, nice_block


def extract_role(text: str):
    text_lower = text.lower()
    for role, keywords in ROLE_TITLE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return role
    return None


def parse_jd(text: str):
    required_block, nice_block = _split_into_sections(text)

    required_skills = extract_skills(required_block) if required_block else []
    nice_to_have_skills = extract_skills(nice_block) if nice_block else []

    # a skill that somehow ends up in both (shouldn't happen with clean
    # section boundaries, but templates aren't the only thing that'll ever
    # feed this parser) counts as required - that's the stricter reading.
    nice_to_have_skills = [s for s in nice_to_have_skills if s not in required_skills]

    role = extract_role(text)

    return {
        "role": role,
        "required_skills": sorted(required_skills),
        "nice_to_have_skills": sorted(nice_to_have_skills),
    }
