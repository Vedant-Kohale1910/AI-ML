"""
save_outputs.py

Step 7 from the study guide: persist the structured output, not just
print it during a notebook run. This is the actual hand-off artifact -
"Structured profiles/jobs" per Section 10 - whatever team picks up
matching/discovery next reads outputs/parsed_resumes.json and
outputs/parsed_jobs.json directly, instead of re-running the parser
themselves.

Run:
    python parser/save_outputs.py
"""

import json
import pandas as pd

from resume_parser import parse_resume
from jd_parser import parse_jd


def main():
    resumes_gt = pd.read_csv("../data/resumes_ground_truth.csv")
    jds_gt = pd.read_csv("../data/job_descriptions_ground_truth.csv")

    parsed_resumes = []
    for _, row in resumes_gt.iterrows():
        text = open(f"data/resumes/{row['resume_id']}.txt").read()
        result = parse_resume(text, name=row["name"])
        result["resume_id"] = row["resume_id"]
        parsed_resumes.append(result)

    parsed_jobs = []
    for _, row in jds_gt.iterrows():
        text = open(f"data/job_descriptions/{row['jd_id']}.txt").read()
        result = parse_jd(text)
        result["jd_id"] = row["jd_id"]
        result["company"] = row["company"]
        parsed_jobs.append(result)

    with open("../outputs/parsed_resumes.json", "w") as f:
        json.dump(parsed_resumes, f, indent=2)
    with open("../outputs/parsed_jobs.json", "w") as f:
        json.dump(parsed_jobs, f, indent=2)

    print(f"wrote {len(parsed_resumes)} parsed resumes -> outputs/parsed_resumes.json")
    print(f"wrote {len(parsed_jobs)} parsed jobs -> outputs/parsed_jobs.json")


if __name__ == "__main__":
    main()
