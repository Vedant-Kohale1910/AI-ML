# Task 13 — Semantic Search & Vector Retrieval
PlaceMux · Phase 3 · Sprint C

## Run
```bash
pip install numpy pandas scikit-learn faiss-cpu
python run_pipeline.py   # builds index, evaluates, writes reports/
python demo.py           # 2-min live demo
```

## What was built
| File | Purpose |
|---|---|
| src/embeddings/generate_embeddings.py | LSA (TF-IDF + SVD 64d) semantic embeddings |
| src/vector_search/faiss_index.py | FAISS IndexFlatIP cosine ANN index |
| src/vector_search/search.py | Keyword, Semantic, Hybrid engines |
| src/evaluation/metrics.py | nDCG@K, MAP@K, Precision@K + labelled eval builder |
| run_pipeline.py | Full pipeline → reports/ |
| demo.py | Live 2-min demo |

## Results
| Metric | Keyword | Semantic | Hybrid (0.7/0.3) |
|---|---|---|---|
| nDCG@5 | 0.9094 | **0.9319** | **0.9365** |
| MAP@5 | 0.8444 | **0.8895** | **0.8963** |
| Latency p50 | 0.04ms | 0.05ms | 0.11ms ✓ SLO |

## Design decisions
- **LSA over sentence-transformers**: offline, no network, reproducible; same semantic property.
- **FAISS IndexFlatIP over pgvector**: zero-dependency demo; swap for production.
- **alpha=0.7 semantic + 0.3 keyword**: tuned on held-out eval set.
