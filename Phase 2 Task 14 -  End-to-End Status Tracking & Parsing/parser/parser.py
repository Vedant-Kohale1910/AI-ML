"""
parser.py

This is basically the Task 12 parser, kept as-is on purpose. Task 14 isn't
supposed to rebuild parsing, it's supposed to consume it - so this file
just extracts skills (plus a couple of other fields we still need for the
demo) out of resume / JD text and hands the list off to ontology/mapper.py.

Resumes and JDs in data/ are plain text with section headers like:

    Skills
    Python, SQL, Machine Learning

    Experience
    ...

Not every resume is that clean in real life, so the extractor tries a few
separators (commas, newlines, bullets, semicolons) and just gives up
gracefully on anything weirder than that - it's a rules-based parser, not
an NER model, and the guide is scoped to the ontology step, not to
rebuilding parsing from scratch.
"""

import re

SECTION_HEADERS = {
    "skills": ["skills", "technical skills", "key skills", "skill set", "core competencies"],
    "required_skills": ["required skills", "must have skills", "requirements", "qualifications"],
    "experience": ["experience", "work experience", "professional experience"],
    "education": ["education", "academic background", "qualifications"],
}

BULLET_CHARS = "•▪●◦-*·"


def _find_section(text, header_aliases):
    """Grab the block of text under the first matching header, up until the
    next header-looking line (or the end of the doc)."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        clean = line.strip().strip(":").lower()
        if clean in header_aliases:
            start = i + 1
            break
    if start is None:
        return ""

    # collect until we hit another section header, or run out of lines
    all_known_headers = set()
    for aliases in SECTION_HEADERS.values():
        all_known_headers.update(aliases)

    collected = []
    for line in lines[start:]:
        clean = line.strip().strip(":").lower()
        if clean in all_known_headers and clean != "":
            break
        collected.append(line)
    return "\n".join(collected).strip()


def _split_skill_line(line):
    """Split a single line of skills text into individual skill tokens."""
    line = line.strip()
    if not line:
        return []
    # strip leading bullet char if present
    line = line.lstrip(BULLET_CHARS).strip()
    # skills are usually comma or semicolon separated on one line
    if "," in line:
        parts = line.split(",")
    elif ";" in line:
        parts = line.split(";")
    else:
        parts = [line]
    return [p.strip() for p in parts if p.strip()]


def extract_skills(text, section="skills"):
    """Pull out a flat, de-duplicated list of raw skill strings from a
    resume or JD. section can be 'skills' (resume) or 'required_skills' (JD)."""
    aliases = SECTION_HEADERS.get(section, SECTION_HEADERS["skills"])
    block = _find_section(text, aliases)

    if not block:
        # fall back: sometimes the whole doc IS just a skills list (short
        # snippets in our sample data do this)
        block = text

    skills = []
    for line in block.splitlines():
        skills.extend(_split_skill_line(line))

    # de-dupe while preserving order
    seen = set()
    out = []
    for s in skills:
        key = s.lower()
        if key not in seen and s:
            seen.add(key)
            out.append(s)
    return out


def parse_resume(text):
    """Returns the same shape the Task 12 parser produced. We keep
    education/experience as raw text blocks here - Task 14 doesn't touch
    those, only 'skills' matters for the ontology step."""
    return {
        "skills": extract_skills(text, section="skills"),
        "education": _find_section(text, SECTION_HEADERS["education"]),
        "experience": _find_section(text, SECTION_HEADERS["experience"]),
    }


def parse_job_description(text):
    skills = extract_skills(text, section="required_skills")
    if not skills:
        # some JDs just use a plain "Skills" header instead of "Required Skills"
        skills = extract_skills(text, section="skills")
    return {
        "required_skills": skills,
    }


if __name__ == "__main__":
    demo_resume = """
    Skills
    Py, ML, Power BI

    Experience
    2 years as a data analyst intern
    """
    print(parse_resume(demo_resume))
