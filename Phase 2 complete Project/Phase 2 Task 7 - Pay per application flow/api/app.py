"""
api/app.py

Serving layer for the matching engine. Loads the model bundle built by
src/train_model.py and exposes it as a small FastAPI app.

Run from the project root:
    uvicorn api.app:app --reload --port 8000

Then try:
    curl -X POST http://localhost:8000/match \
        -H "Content-Type: application/json" \
        -d '{"skills": "Python, SQL, Machine Learning"}'
"""

import os
import sys
import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# so we can import src/matching.py whether this is started from the repo
# root or from inside api/ - both happen depending on who runs it.
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))
from matching import parse_skills, explain_match, hybrid_score  # noqa: E402

MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "models", "matching_model.pkl")

app = FastAPI(title="PlaceMux Matching API", version="0.1.0")

_model = None  # lazy-loaded, see get_model()


def get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise RuntimeError(
                f"no model found at {MODEL_PATH}. run `python src/train_model.py` first."
            )
        _model = joblib.load(MODEL_PATH)
    return _model


class MatchRequest(BaseModel):
    skills: str
    top_n: int | None = 5


class MatchResponse(BaseModel):
    jobs: list


@app.get("/health")
def health():
    # mostly here so the founder / whoever wires this into the journey
    # has something to hit before sending real traffic at it.
    model_ready = os.path.exists(MODEL_PATH)
    return {"status": "ok", "model_loaded": model_ready}


@app.post("/match", response_model=MatchResponse)
def match(req: MatchRequest):
    student_skills = parse_skills(req.skills)
    if not student_skills:
        raise HTTPException(status_code=400, detail="couldn't parse any skills from the input - check formatting (comma separated)")

    model = get_model()
    vectorizer = model["vectorizer"]
    job_matrix = model["job_matrix"]
    jobs_df = model["jobs_df"]
    job_skill_lists = model["job_skill_lists"]
    alpha = model["alpha"]

    from matching import skills_to_doc, baseline_score
    from sklearn.metrics.pairwise import cosine_similarity

    student_doc = skills_to_doc(student_skills)
    student_vec = vectorizer.transform([student_doc])
    tfidf_sims = cosine_similarity(student_vec, job_matrix)[0]

    results = []
    for i, row in jobs_df.iterrows():
        job_skills = job_skill_lists[i]
        overlap = baseline_score(student_skills, job_skills)
        score = hybrid_score(tfidf_sims[i], overlap, alpha)
        results.append({
            "job_id": int(row["job_id"]),
            "title": row["title"],
            "company": row["company"],
            "score": round(float(score), 4),
            "explanation": explain_match(student_skills, job_skills),
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    top_n = req.top_n or 5
    return {"jobs": results[:top_n]}
