"""질문 → 매뉴얼 검색(하이브리드: dense+sparse+payload exact). P0 스텁(→ P4)."""
from __future__ import annotations


class Retriever:
    def __init__(self, embedder, store):
        self.embedder = embedder
        self.store = store

    def retrieve(self, question: str, role: str = "branch", top_k: int = 5) -> list:
        # TODO(P4): KURE dense + sparse + payload(role/screen) 필터 → RRF.
        return []
