"""
Basic sanity tests. Nothing fancy - just enough to catch a broken ontology
load or a regression in the normalization logic before it reaches a demo.

Run with: pytest tests/
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from ontology.mapper import SkillOntologyMapper, normalize
from parser.parser import parse_resume, parse_job_description


def test_normalize_collapses_variants():
    assert normalize("Power-BI") == normalize("Power BI")
    assert normalize("  Python3 ") == "python3"


def test_exact_alias_match():
    mapper = SkillOntologyMapper()
    result = mapper.map_skill("Py")
    assert result["standard"] == "Python"
    assert result["method"] == "exact"
    assert result["confidence"] == 1.0


def test_fuzzy_match_catches_typo():
    mapper = SkillOntologyMapper()
    result = mapper.map_skill("Machinee Learning")
    assert result["standard"] == "Machine Learning"
    assert result["method"] == "fuzzy"
    assert result["confidence"] > 0.8


def test_unknown_skill_stays_unmapped_not_dropped():
    mapper = SkillOntologyMapper()
    result = mapper.map_skill("Photoshop")
    assert result["method"] == "unmapped"
    # should not disappear - still comes back as something
    assert result["standard"]


def test_map_skill_list_dedupes_standard_skills():
    mapper = SkillOntologyMapper()
    out = mapper.map_skill_list(["Py", "Python Programming", "ML"])
    assert out["standard_skills"] == ["Python", "Machine Learning"]
    assert len(out["mappings"]) == 3


def test_parser_extracts_skills_section():
    text = "Skills\nPy, ML, Power BI\n\nEducation\nB.Tech CS"
    parsed = parse_resume(text)
    assert parsed["skills"] == ["Py", "ML", "Power BI"]


def test_jd_parser_extracts_required_skills():
    text = "Required Skills\nPython, SQL, Machine Learning\n\nQualifications\nBachelor's degree"
    parsed = parse_job_description(text)
    assert parsed["required_skills"] == ["Python", "SQL", "Machine Learning"]
