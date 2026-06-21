import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def load_data(students_path="data/students.csv", jobs_path="data/jobs.csv"):
    students = pd.read_csv(students_path)
    jobs = pd.read_csv(jobs_path)
    return students, jobs


def normalize_skills(skill_str):
    # clean up whatever the user typed, handle NaN gracefully
    if pd.isna(skill_str) or str(skill_str).strip() == "":
        return set()
    return {s.strip().lower() for s in skill_str.split(",")}


def skill_overlap_score(candidate_skills, required_skills):
    c = normalize_skills(candidate_skills)
    r = normalize_skills(required_skills)
    if not r:
        return 0.0
    matched = c & r
    return round(len(matched) / len(r), 4)


def get_matched_skills(candidate_skills, required_skills):
    c = normalize_skills(candidate_skills)
    r = normalize_skills(required_skills)
    return sorted(c & r)


def get_missing_skills(candidate_skills, required_skills):
    c = normalize_skills(candidate_skills)
    r = normalize_skills(required_skills)
    return sorted(r - c)


def tfidf_similarity(query_skills, corpus_skills_list):
    # treat each skill string as a tiny document and do cosine sim
    # commas -> spaces so TF-IDF sees individual skill tokens
    all_docs = [query_skills] + corpus_skills_list
    cleaned = [d.replace(",", " ").lower() for d in all_docs]

    vec = TfidfVectorizer(
        analyzer="word",
        token_pattern=r"[a-zA-Z0-9_\+\#\.]+",
        ngram_range=(1, 2)
    )

    try:
        mat = vec.fit_transform(cleaned)
    except ValueError:
        return np.zeros(len(corpus_skills_list))

    sims = cosine_similarity(mat[0:1], mat[1:]).flatten()
    return sims


def compute_final_score(overlap, tfidf_sim, comm_score=None):
    # weights tuned manually after a few runs
    # overlap matters most, tfidf catches partial matches, comm is minor
    w_overlap = 0.5
    w_tfidf = 0.4
    w_comm = 0.1

    comm_val = 0.0
    if comm_score is not None:
        comm_val = float(comm_score) / 100.0

    score = w_overlap * overlap + w_tfidf * tfidf_sim + w_comm * comm_val
    return min(round(score, 4), 1.0)


#job ranking (for students)
def rank_jobs_for_student(student, jobs_df, top_n=None):
    skills = str(student["skills"])
    comm = student.get("communication_score", None)
    exp = student.get("experience_years", 0)

    job_skill_list = jobs_df["required_skills"].astype(str).tolist()
    sims = tfidf_similarity(skills, job_skill_list)

    idx_list = list(jobs_df.index)
    results = []

    for idx, job in jobs_df.iterrows():
        overlap = skill_overlap_score(skills, job["required_skills"])
        sim = float(sims[idx_list.index(idx)])
        score = compute_final_score(overlap, sim, comm)

        matched = get_matched_skills(skills, job["required_skills"])
        missing = get_missing_skills(skills, job["required_skills"])

        # small bonus if they meet the exp requirement
        min_exp = int(job.get("min_experience", 0))
        exp_bump = 0.02 if int(exp) >= min_exp else 0.0
        final = min(score + exp_bump, 1.0)

        results.append({
            "job_id": job["job_id"],
            "title": job["title"],
            "company": job.get("company", "N/A"),
            "location": job.get("location", "N/A"),
            "salary_range": job.get("salary_range", "N/A"),
            "match_score": round(final * 100, 1),
            "skill_overlap_pct": round(overlap * 100, 1),
            "matched_skills": matched,
            "missing_skills": missing,
            "required_skills": [s.strip() for s in job["required_skills"].split(",")],
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_n] if top_n else results


def explain_job_match(student_name, job):
    lines = [
        f"Student    : {student_name}",
        f"Job        : {job['title']} @ {job['company']}",
        f"Match Score: {job['match_score']}%",
        "",
        "Skill Breakdown:",
    ]
    for s in job["matched_skills"]:
        lines.append(f"  [MATCH]   {s.title()}")
    for s in job["missing_skills"]:
        lines.append(f"  [MISSING] {s.title()}")
    if not job["matched_skills"]:
        lines.append("  no matching skills found")
    return "\n".join(lines)


#candidate ranking (for companies)
def rank_candidates_for_job(job, students_df, top_n=None):
    job_skills = str(job["required_skills"])
    min_exp = int(job.get("min_experience", 0))

    student_skill_list = students_df["skills"].astype(str).tolist()
    sims = tfidf_similarity(job_skills, student_skill_list)

    idx_list = list(students_df.index)
    results = []

    for idx, student in students_df.iterrows():
        overlap = skill_overlap_score(student["skills"], job_skills)
        sim = float(sims[idx_list.index(idx)])
        comm = student.get("communication_score", None)
        score = compute_final_score(overlap, sim, comm)

        exp = int(student.get("experience_years", 0))
        exp_bump = 0.02 if exp >= min_exp else 0.0
        final = min(score + exp_bump, 1.0)

        matched = get_matched_skills(student["skills"], job_skills)
        missing = get_missing_skills(student["skills"], job_skills)

        results.append({
            "student_id": student["student_id"],
            "name": student["name"],
            "skills": student["skills"],
            "experience_years": exp,
            "location": student.get("location", "N/A"),
            "communication_score": comm,
            "match_score": round(final * 100, 1),
            "skill_overlap_pct": round(overlap * 100, 1),
            "matched_skills": matched,
            "missing_skills": missing,
        })

    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:top_n] if top_n else results


def explain_candidate_match(job_title, candidate):
    lines = [
        f"Candidate  : {candidate['name']}",
        f"Job        : {job_title}",
        f"Match Score: {candidate['match_score']}%",
        f"Experience : {candidate['experience_years']} yr(s)",
        f"Comm Score : {candidate['communication_score']}/100",
        "",
        "Skill Breakdown:",
    ]
    for s in candidate["matched_skills"]:
        lines.append(f"  [MATCH]   {s.title()}")
    for s in candidate["missing_skills"]:
        lines.append(f"  [MISSING] {s.title()}")
    if not candidate["matched_skills"]:
        lines.append("  no matching skills found")
    return "\n".join(lines)


#metrics
def compute_metrics(ranked, relevance_threshold=60.0, top_k=5):
    top = ranked[:top_k]

    total_relevant = sum(1 for r in ranked if r["match_score"] >= relevance_threshold)
    tp = sum(1 for r in top if r["match_score"] >= relevance_threshold)
    fp = sum(1 for r in top if r["match_score"] < relevance_threshold)
    total_neg = sum(1 for r in ranked if r["match_score"] < relevance_threshold)

    precision = tp / top_k if top_k > 0 else 0.0
    recall = tp / total_relevant if total_relevant > 0 else 0.0
    fpr = fp / total_neg if total_neg > 0 else 0.0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "false_positive_rate": round(fpr, 3),
        "true_positives": tp,
        "false_positives": fp,
        "total_relevant": total_relevant,
        "top_k": top_k,
        "relevance_threshold": relevance_threshold,
    }
