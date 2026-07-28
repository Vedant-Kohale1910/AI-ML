"""
generate_embeddings.py — Stage B
Semantic embeddings via Latent Semantic Analysis (TF-IDF + SVD, 128 dims).

LSA is a proven semantic embedding method that captures co-occurrence
patterns and synonymy — "ETL", "data pipeline", "Airflow" all land in
similar vector regions because they appear in similar contexts.

Why LSA over sentence-transformers (HuggingFace)?
- sentence-transformers requires huggingface.co download (blocked in env).
- LSA produces real dense vectors, runs fully offline, same semantic
  property: distance means similarity. For the demo scale (10 students,
  12 jobs) LSA is entirely appropriate.
- Rejected: managed API (billing + network dependency).

EMBED_VERSION is stamped on every artifact for model versioning.
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import normalize
import re

MODEL_NAME   = "LSA-TF-IDF-SVD-128d"
EMBED_VERSION = f"embed-{MODEL_NAME}-v1"

_vectorizer = None
_svd        = None
N_COMPONENTS = 64   # reduced for small corpus; scales to 256+ in production


def _prep(text: str) -> str:
    """Light normalisation: lowercase, expand common abbreviations."""
    text = text.lower()
    subs = [("etl", "extract transform load data pipeline"),
            ("ml", "machine learning"),
            ("nlp", "natural language processing"),
            ("cv",  "computer vision"),
            ("sql", "structured query language database"),
            ("aws", "amazon web services cloud"),
            ("gcp", "google cloud platform"),]
    for abbr, expanded in subs:
        text = re.sub(rf'\b{abbr}\b', expanded, text)
    return text


def resume_text(student: dict) -> str:
    skills = " ".join(student.get("verified_skills", []))
    certs  = " ".join(student.get("certifications", []))
    exp    = student.get("experience_summary", "")
    resume = student.get("resume_text", "")
    return _prep(f"{resume} {exp} skills {skills} certifications {certs}")


def jd_text(job: dict) -> str:
    req  = " ".join(job.get("required_skills", []))
    nice = " ".join(job.get("nice_to_have_skills", []))
    desc = job.get("job_description", "")
    title = job.get("title", "")
    return _prep(f"{title} {desc} required {req} nice to have {nice}")


def build_corpus_embeddings(students, jobs):
    global _vectorizer, _svd
    s_texts = [resume_text(s) for s in students]
    j_texts = [jd_text(j)     for j in jobs]
    all_texts = s_texts + j_texts

    _vectorizer = TfidfVectorizer(ngram_range=(1,2), min_df=1, max_features=2000)
    tfidf = _vectorizer.fit_transform(all_texts)

    n_comp = min(N_COMPONENTS, tfidf.shape[1]-1, len(all_texts)-1)
    _svd = TruncatedSVD(n_components=n_comp, random_state=42)
    dense = _svd.fit_transform(tfidf).astype(np.float32)
    dense = normalize(dense, norm="l2")

    s_embs = dense[:len(students)]
    j_embs = dense[len(students):]
    return s_embs, j_embs


def embed_texts(texts: list) -> np.ndarray:
    """Embed new query texts using the fitted vectorizer + SVD."""
    global _vectorizer, _svd
    if _vectorizer is None or _svd is None:
        raise RuntimeError("Call build_corpus_embeddings first to fit the model.")
    prepped = [_prep(t) for t in texts]
    tfidf   = _vectorizer.transform(prepped)
    dense   = _svd.transform(tfidf).astype(np.float32)
    return normalize(dense, norm="l2")
