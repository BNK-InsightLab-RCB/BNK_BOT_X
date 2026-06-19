"""질문 → 매뉴얼 검색(하이브리드: dense + Qdrant sparse, payload role 필터).

- dense: KURE 임베딩(미설치 시 해시 폴백) cosine.
- sparse: Qdrant native sparse vector. 한글 표기와 내부 식별자 exact-ish recall 보강.
- 둘을 합쳐 랭킹. 게이트는 dense/lexical의 *절대값*으로 회피를 판단(P4 gate).
"""
from __future__ import annotations


class Retriever:
    def __init__(self, embedder, store):
        self.embedder = embedder
        self.store = store

    def retrieve(self, question: str, role: str = "branch", top_k: int = 5) -> list[dict]:
        if self.store is None:
            return []
        qvec = self.embedder.embed_one(question)
        raw_dense = self.store.search(qvec, top_k=max(top_k, 10), role=role, using="dense")

        q_sparse = self.embedder.get_sparse_vector(question)
        raw_sparse = []
        if q_sparse:
            try:
                raw_sparse = self.store.search(
                    q_sparse, top_k=max(top_k, 10), role=role, using="sparse"
                )
            except Exception:
                raw_sparse = []  # sparse 장애가 답변 경로 전체를 깨지 않도록 dense fallback

        hits_by_id: dict[str, dict] = {}
        for h in raw_dense:
            hits_by_id[str(h.id)] = {
                "payload": h.payload,
                "dense": max(float(h.score), 0.0),
                "sparse_score": 0.0,
            }
        for h in raw_sparse:
            key = str(h.id)
            if key not in hits_by_id:
                hits_by_id[key] = {"payload": h.payload, "dense": 0.0, "sparse_score": 0.0}
            hits_by_id[key]["sparse_score"] = max(float(h.score), 0.0)

        q_len = max(len(self.embedder.bigrams(question)), 1)
        hits: list[dict] = []
        for item in hits_by_id.values():
            lexical = min(item["sparse_score"] / q_len, 1.0)
            dense = item["dense"]
            hits.append(
                {
                    "payload": item["payload"],
                    "dense": dense,
                    "lexical": lexical,
                    "score": dense + 0.5 * lexical,
                }
            )
        hits.sort(key=lambda x: x["score"], reverse=True)
        return hits[:top_k]
