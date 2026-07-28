"""
search.py — Three retrieval modes:
  keyword_search  : TF-IDF BM25-style (baseline)
  semantic_search : FAISS cosine over embeddings
  hybrid_search   : alpha * semantic + (1-alpha) * keyword  [alpha=0.7]
"""
import math
import re
import time
import numpy as np


# ── Keyword search (TF-IDF cosine, no external deps) ──────────────────────

def _tokenise(text: str) -> list:
    return re.findall(r"[a-z0-9]+", text.lower())


def _tfidf_vectors(docs: list):
    from collections import Counter
    tokenised = [_tokenise(d) for d in docs]
    df = {}
    for tok in tokenised:
        for w in set(tok):
            df[w] = df.get(w, 0) + 1
    N = len(docs)
    vocab = list(df.keys())
    v2i = {w: i for i, w in enumerate(vocab)}
    idf = {w: math.log((N + 1) / (df[w] + 1)) + 1 for w in vocab}

    vecs = []
    for tok in tokenised:
        tf = Counter(tok)
        total = max(sum(tf.values()), 1)
        vec = np.zeros(len(vocab), dtype=np.float32)
        for w, c in tf.items():
            if w in v2i:
                vec[v2i[w]] = (c / total) * idf[w]
        n = np.linalg.norm(vec)
        if n > 0:
            vec /= n
        vecs.append(vec)
    return np.array(vecs), vocab, idf, v2i


class KeywordSearchEngine:
    def __init__(self, docs: list, doc_ids: list):
        self.doc_ids = doc_ids
        self.vecs, self.vocab, self.idf, self.v2i = _tfidf_vectors(docs)

    def search(self, query: str, top_k: int = 5):
        t0 = time.perf_counter()
        qtok = _tokenise(query)
        from collections import Counter
        tf = Counter(qtok)
        total = max(sum(tf.values()), 1)
        qvec = np.zeros(len(self.vocab), dtype=np.float32)
        for w, c in tf.items():
            if w in self.v2i:
                qvec[self.v2i[w]] = (c / total) * self.idf.get(w, 1.0)
        n = np.linalg.norm(qvec)
        if n > 0:
            qvec /= n
        scores = self.vecs @ qvec
        top_idx = np.argsort(scores)[::-1][:top_k]
        lat = round((time.perf_counter() - t0) * 1000, 3)
        return (
            [self.doc_ids[i] for i in top_idx],
            [round(float(scores[i]), 4) for i in top_idx],
            lat
        )


# ── Semantic search ────────────────────────────────────────────────────────

class SemanticSearchEngine:
    def __init__(self, index, embed_fn):
        self.index   = index
        self.embed_fn = embed_fn   # callable: str -> np.ndarray
        self.enabled = True        # set False to simulate failure

    def search(self, query: str, top_k: int = 5):
        if not self.enabled:
            raise RuntimeError("SemanticSearchEngine: vector index unavailable (failure scenario)")
        qemb = self.embed_fn([query])[0]
        return self.index.search(qemb, top_k)   # ids, scores, lat_ms


# ── Hybrid search ──────────────────────────────────────────────────────────

ALPHA = 0.7   # weight for semantic; 1-alpha for keyword

class HybridSearchEngine:
    def __init__(self, semantic: SemanticSearchEngine, keyword: KeywordSearchEngine,
                 alpha: float = ALPHA):
        self.semantic = semantic
        self.keyword  = keyword
        self.alpha    = alpha

    def search(self, query: str, top_k: int = 5, all_ids: list = None):
        try:
            s_ids, s_scores, s_lat = self.semantic.search(query, top_k * 2)
            semantic_ok = True
        except RuntimeError:
            s_ids, s_scores, s_lat = [], [], 0
            semantic_ok = False

        k_ids, k_scores, k_lat = self.keyword.search(query, top_k * 2)

        # Normalise to [0,1] then blend
        def norm(scores):
            mx = max(scores) if scores else 1
            return [s / max(mx, 1e-9) for s in scores]

        combined = {}
        for did, sc in zip(s_ids, norm(s_scores)):
            combined[did] = combined.get(did, 0) + self.alpha * sc
        for did, sc in zip(k_ids, norm(k_scores)):
            combined[did] = combined.get(did, 0) + (1 - self.alpha) * sc

        ranked = sorted(combined.items(), key=lambda x: -x[1])[:top_k]
        ids    = [r[0] for r in ranked]
        scores = [round(r[1], 4) for r in ranked]
        return ids, scores, round(s_lat + k_lat, 3), semantic_ok
