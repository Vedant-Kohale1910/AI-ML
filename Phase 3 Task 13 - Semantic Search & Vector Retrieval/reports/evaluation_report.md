# Evaluation Report — Task 13: Semantic Search & Vector Retrieval

Embedding model: `embed-LSA-TF-IDF-SVD-128d-v1`  |  FAISS IndexFlatIP

## Offline metrics on labelled eval set

| Metric | Keyword (baseline) | Semantic | Hybrid (0.7/0.3) |
|---|---|---|---|
| ndcg@5 | 0.9094 | 0.9319 | 0.9365 |
| map@5 | 0.8444 | 0.8895 | 0.8963 |
| precision@5 | 0.3778 | 0.3556 | 0.3556 |

N queries: 9 (from real interaction logs, not cherry-picked)

## Latency (p50)

| Method | p50 ms | SLO <200ms |
|---|---|---|
