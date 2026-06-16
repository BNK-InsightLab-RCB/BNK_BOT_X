"""질문 → 매뉴얼 검색(하이브리드: dense + lexical, payload role 필터).

- dense: KURE 임베딩(미설치 시 해시 폴백) cosine.
- lexical: 질문 vs 매뉴얼 핵심필드(screen_ko·table_ko·action)의 char-bigram 겹침.
  한국어 조사 변형(저장이/저장을)에 강하도록 형태소 대신 bigram 사용.
- 둘을 합쳐 랭킹. 게이트는 dense/lexical의 *절대값*으로 회피를 판단(P4 gate).
"""
from __future__ import annotations

import re


def _bigrams(text: str) -> set[str]:
    t = re.sub(r"[^0-9a-z가-힣]", "", (text or "").lower())
    return {t[i : i + 2] for i in range(len(t) - 1)}


def _overlap(q: set[str], p: set[str]) -> float:
    return len(q & p) / len(q) if q else 0.0


class Retriever:
    def __init__(self, embedder, store):
        self.embedder = embedder
        self.store = store

    def retrieve(self, question: str, role: str = "branch", top_k: int = 5) -> list[dict]:
        if self.store is None:
            return []
        qvec = self.embedder.embed_one(question)
        raw = self.store.search(qvec, top_k=max(top_k, 10), role=role)
        qb = _bigrams(question)
        hits: list[dict] = []
        for h in raw:
            p = h.payload
            concise = f"{p.get('screen_ko', '')} {p.get('action', '')} {' '.join(p.get('table_ko', []))}"
            lexical = _overlap(qb, _bigrams(concise))
            dense = max(float(h.score), 0.0)
            hits.append(
                {"payload": p, "dense": dense, "lexical": lexical, "score": dense + 0.5 * lexical}
            )
        hits.sort(key=lambda x: x["score"], reverse=True)
        return hits[:top_k]
