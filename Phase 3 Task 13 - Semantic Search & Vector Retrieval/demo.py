"""Task 13 — Live demo.  Run: python demo.py"""
import json, os, sys
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from embeddings.generate_embeddings import build_corpus_embeddings, resume_text, embed_texts, EMBED_VERSION
from vector_search.faiss_index import FaissIndex
from vector_search.search import KeywordSearchEngine, SemanticSearchEngine, HybridSearchEngine

BASE = os.path.dirname(__file__)

def sep(t): print(f"\n{'='*58}\n  {t}\n{'='*58}")

def main():
    with open(os.path.join(BASE,"data/sample_students.json")) as f: students = json.load(f)
    with open(os.path.join(BASE,"data/sample_jobs.json"))    as f: jobs     = json.load(f)
    interactions = pd.read_csv(os.path.join(BASE,"data/event_logs.csv"))
    smap = {s["student_id"]: s for s in students}

    # Build engines (same as pipeline)
    s_embs, _ = build_corpus_embeddings(students, jobs)
    student_ids = [s["student_id"] for s in students]
    s_texts = [resume_text(s) for s in students]

    idx = FaissIndex(s_embs.shape[1])
    idx.add(s_embs, student_ids)
    kw  = KeywordSearchEngine(s_texts, student_ids)
    sem = SemanticSearchEngine(idx, embed_fn=embed_texts)
    hyb = HybridSearchEngine(sem, kw, alpha=0.7)

    sep("STEP 1 — What we built")
    print(f"  Corpus: {len(students)} resumes + {len(jobs)} JDs")
    print(f"  Embedding: {EMBED_VERSION}  |  dim={s_embs.shape[1]}")
    print(f"  FAISS IndexFlatIP: {idx.size()} vectors indexed")

    sep("STEP 2 — Keyword search (baseline)")
    q = "someone who can build data pipelines"
    print(f"  Query: \"{q}\"")
    k_ids, k_scores, k_lat = kw.search(q, top_k=5)
    for rank, (did, sc) in enumerate(zip(k_ids, k_scores), 1):
        s = smap.get(did, {})
        print(f"  {rank}. {s.get('name','?'):<18}  score={sc:.3f}  skills={s.get('verified_skills',[])}")
    print(f"  Latency: {k_lat} ms")

    sep("STEP 3 — Semantic search (our model)")
    print(f"  Query: \"{q}\"")
    s_ids, s_scores, s_lat = sem.search(q, top_k=5)
    for rank, (did, sc) in enumerate(zip(s_ids, s_scores), 1):
        s = smap.get(did, {})
        print(f"  {rank}. {s.get('name','?'):<18}  similarity={sc:.3f}  skills={s.get('verified_skills',[])}")
    print(f"  Latency: {s_lat} ms")

    sep("STEP 4 — Explain top semantic result")
    top = smap.get(s_ids[0], {})
    print(f"  Candidate: {top.get('name')}")
    print(f"  Query meaning: 'data pipelines' → ETL, Spark, Airflow, Data Engineering")
    print(f"  Why found:  Skills {top.get('verified_skills',[])} co-occur in same")
    print(f"              semantic space as 'data pipelines' in the LSA embedding.")
    print(f"  Similarity score: {s_scores[0]:.3f}")
    print(f"  Would keyword match? {'Yes' if top.get('student_id') in k_ids else 'Possibly not — no exact keyword overlap'}")

    sep("STEP 5 — Hybrid search (semantic 70% + keyword 30%)")
    h_ids, h_scores, h_lat, sem_ok = hyb.search(q, top_k=5)
    for rank, (did, sc) in enumerate(zip(h_ids, h_scores), 1):
        s = smap.get(did, {})
        print(f"  {rank}. {s.get('name','?'):<18}  hybrid_score={sc:.3f}")
    print(f"  Latency: {h_lat} ms")

    sep("STEP 6 — Offline eval numbers")
    print("  From reports/semantic_vs_keyword.csv:")
    with open(os.path.join(BASE,"reports/semantic_vs_keyword.csv")) as f:
        for line in f: print("  " + line.rstrip())

    sep("STEP 7 — FAILURE SCENARIO: semantic index disabled")
    sem.enabled = False
    try:
        sem.search(q)
    except RuntimeError as e:
        print(f"  Semantic engine raised: {e}")
    print("  → Hybrid falls back to keyword-only automatically:")
    h_ids2, h_scores2, h_lat2, sem_ok2 = hyb.search(q, top_k=3)
    print(f"  semantic_ok={sem_ok2} | still returned {len(h_ids2)} results | no crash")
    sem.enabled = True   # restore

    sep("DEMO COMPLETE")
    print("  Model version:", EMBED_VERSION)
    print("  Reports: reports/semantic_vs_keyword.csv, evaluation_report.md")

if __name__ == "__main__":
    main()
