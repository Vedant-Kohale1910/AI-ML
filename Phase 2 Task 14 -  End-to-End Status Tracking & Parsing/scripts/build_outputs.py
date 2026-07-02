"""
build_outputs.py

Runs the whole pipeline (parse -> ontology map) over every sample resume
and JD in data/, and dumps the standardized result to
outputs/standardized_profiles.json. This is what gets fed to the matching
engine (Task 7) - it's the actual hand-off artifact for this task.

Run with: python scripts/build_outputs.py
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from parser.parser import parse_resume, parse_job_description
from ontology.mapper import SkillOntologyMapper

BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_DIR = BASE_DIR / "data" / "resumes"
JD_DIR = BASE_DIR / "data" / "job_descriptions"
OUT_FILE = BASE_DIR / "outputs" / "standardized_profiles.json"


def process_resumes(mapper):
    profiles = []
    for path in sorted(RESUME_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        parsed = parse_resume(text)
        mapped = mapper.map_skill_list(parsed["skills"])
        profiles.append({
            "source_file": path.name,
            "original_skills": mapped["original_skills"],
            "standard_skills": mapped["standard_skills"],
            "mappings": mapped["mappings"],
        })
    return profiles


def process_jds(mapper):
    postings = []
    for path in sorted(JD_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8")
        parsed = parse_job_description(text)
        mapped = mapper.map_skill_list(parsed["required_skills"])
        postings.append({
            "source_file": path.name,
            "original_required_skills": mapped["original_skills"],
            "standard_required_skills": mapped["standard_skills"],
            "mappings": mapped["mappings"],
        })
    return postings


def main():
    mapper = SkillOntologyMapper()
    resumes = process_resumes(mapper)
    jds = process_jds(mapper)

    # quick coverage stat - how many raw skills we actually recognised,
    # good sanity check to print alongside the dump
    all_mappings = [m for r in resumes for m in r["mappings"]] + [m for j in jds for m in j["mappings"]]
    unmapped_count = sum(1 for m in all_mappings if m["method"] == "unmapped")
    coverage = 1 - (unmapped_count / len(all_mappings)) if all_mappings else 0

    output = {
        "generated_from": {
            "resumes": len(resumes),
            "job_descriptions": len(jds),
        },
        "ontology_coverage": round(coverage, 4),
        "resumes": resumes,
        "job_descriptions": jds,
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)

    print(f"Processed {len(resumes)} resumes and {len(jds)} JDs.")
    print(f"Ontology coverage on raw skills: {coverage:.2%} ({unmapped_count} unmapped out of {len(all_mappings)})")
    print(f"Saved -> {OUT_FILE}")


if __name__ == "__main__":
    main()
