"""
faiss_index.py — ANN index using FAISS (Flat L2 for exact search at demo scale;
swap to IVF for 100k+ vectors in production).
"""
import faiss
import numpy as np
import time


class FaissIndex:
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)   # Inner Product = cosine after L2-norm
        self.ids = []   # maps position -> original id

    def add(self, embeddings: np.ndarray, ids: list):
        # L2-normalise so inner product == cosine similarity
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        normed = embeddings / np.maximum(norms, 1e-9)
        self.index.add(normed.astype(np.float32))
        self.ids.extend(ids)

    def search(self, query_emb: np.ndarray, top_k: int = 5):
        """Returns (ids, scores, latency_ms)."""
        t0 = time.perf_counter()
        norm = np.linalg.norm(query_emb)
        q = (query_emb / max(norm, 1e-9)).reshape(1, -1).astype(np.float32)
        scores, positions = self.index.search(q, top_k)
        lat = round((time.perf_counter() - t0) * 1000, 3)
        result_ids = [self.ids[p] for p in positions[0] if p >= 0]
        result_scores = [round(float(s), 4) for s in scores[0] if s > -1]
        return result_ids, result_scores, lat

    def size(self):
        return self.index.ntotal
