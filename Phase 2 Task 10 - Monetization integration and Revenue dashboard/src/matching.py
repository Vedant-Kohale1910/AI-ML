"""
matching.py

The actual "matching tune" logic. Three scoring functions, going from
dumbest to smartest, plus an explain function so every score comes with
a plain-English reason (no black box, per the study guide).

    1. baseline_score   - skill overlap. coverage of what the job asked for.
    2. tfidf_score       - TF-IDF + cosine similarity over skill text.
    3. hybrid_score       - weighted blend of the two, weight tuned on the
                            validation split (see evaluate.py). This is what
                            actually ships in matching_model.pkl.

Everything here works on plain comma-separated skill strings, same format
as the CSVs, so it's easy to wire into the FastAPI layer without an extra
translation step.
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# people don't all type skills the same way. handling a handful of the
# common ones here beats pretending the data is always clean.
SKILL_ALIASES = {
    "ml": "Machine Learning",
    "dl": "Deep Learning",
    "powerbi": "Power BI",
    "power bi": "Power BI",
    "js": "JavaScript",
    "ts": "TypeScript",
    "k8s": "Kubernetes",
    "restapi": "REST API",
    "rest api": "REST API",
    "ci/cd": "CI/CD",
    "node": "Node.js",
    "nodejs": "Node.js",
}


def parse_skills(skill_str):
    """'Python, sql,  ML' -> ['Python', 'SQL', 'Machine Learning'] (normalised, deduped)"""
    if not skill_str or not isinstance(skill_str, str):
        return []
    raw = [s.strip() for s in skill_str.split(",") if s.strip()]
    out = []
    for s in raw:
        key = s.lower()
        norm = SKILL_ALIASES.get(key, s)
        if norm not in out:
            out.append(norm)
    return out


def _to_token(skill):
    # TF-IDF tokenises on whitespace by default, which would split
    # "Power BI" into two separate tokens and lose the skill as a unit.
    # underscoring multi-word skills keeps each one atomic.
    return skill.lower().replace(" ", "_").replace("/", "_")


def skills_to_doc(skill_list):
    return " ".join(_to_token(s) for s in skill_list)


def baseline_score(student_skills, job_skills):
    """
    Dumb baseline: what fraction of the job's required skills does the
    student actually have? This is the number every later model has to beat.
    """
    if not job_skills:
        return 0.0
    student_set = set(s.lower() for s in student_skills)
    job_set = set(s.lower() for s in job_skills)
    matched = student_set & job_set
    return len(matched) / len(job_set)


class TfidfMatcher:
    """Fits one TF-IDF space over a fixed pool of jobs, then scores any
    student's skills against every job in that pool."""

    def __init__(self, jobs_df):
        self.jobs_df = jobs_df.reset_index(drop=True)
        self.job_skill_lists = [parse_skills(s) for s in self.jobs_df["required_skills"]]
        job_docs = [skills_to_doc(sk) for sk in self.job_skill_lists]

        self.vectorizer = TfidfVectorizer()
        self.job_matrix = self.vectorizer.fit_transform(job_docs)

    def score_all(self, student_skills):
        """Returns a numpy array of cosine similarity, one score per job,
        in the same row order as self.jobs_df."""
        student_doc = skills_to_doc(student_skills)
        student_vec = self.vectorizer.transform([student_doc])
        sims = cosine_similarity(student_vec, self.job_matrix)[0]
        return sims

    def baseline_score_all(self, student_skills):
        return [baseline_score(student_skills, job_sk) for job_sk in self.job_skill_lists]


def hybrid_score(tfidf_sim, overlap_score, alpha):
    """alpha=1 -> pure tfidf, alpha=0 -> pure baseline overlap"""
    return alpha * tfidf_sim + (1 - alpha) * overlap_score


def explain_match(student_skills, job_skills):
    """Plain-English breakdown for a single student/job pair - this is
    what gets shown in the demo and returned by the API alongside the score."""
    student_set = set(s.lower() for s in student_skills)
    job_set = set(s.lower() for s in job_skills)

    matched = [s for s in job_skills if s.lower() in student_set]
    missing = [s for s in job_skills if s.lower() not in student_set]

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "match_count": len(matched),
        "required_count": len(job_skills),
    }


def rank_jobs(student_skills, matcher: TfidfMatcher, alpha=0.6, top_n=5):
    """The function the API actually calls. Scores every job, blends
    baseline + tfidf using the tuned alpha, sorts, returns the top N with
    explanations attached."""
    tfidf_sims = matcher.score_all(student_skills)
    overlaps = matcher.baseline_score_all(student_skills)

    results = []
    for i, row in matcher.jobs_df.iterrows():
        job_skills = matcher.job_skill_lists[i]
        score = hybrid_score(tfidf_sims[i], overlaps[i], alpha)
        results.append({
            "job_id": int(row["job_id"]),
            "title": row["title"],
            "company": row["company"],
            "score": round(float(score), 4),
            "explanation": explain_match(student_skills, job_skills),
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    return results[:top_n]
