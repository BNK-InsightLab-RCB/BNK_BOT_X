"""RAG 오케스트레이션: 검색 → 정밀도 게이트 → (충분)다듬기 / (부족)핸드오프.

P0: 게이트가 항상 회피 → 모든 질문이 핸드오프 응답. P4에서 다듬기 경로 채움.
"""
from __future__ import annotations

from src.chat.schemas import QueryResponse

HANDOFF_MSG = (
    "현재 확실히 답할 수 있는 근거(검수된 매뉴얼)를 찾지 못했습니다. "
    "담당 개발자에게 문의해 주세요."
)


class ChatService:
    def __init__(self, retriever, gate, generator):
        self.retriever = retriever
        self.gate = gate
        self.generator = generator

    def answer(self, question: str, role: str = "branch", top_k: int = 5) -> QueryResponse:
        hits = self.retriever.retrieve(question, role=role, top_k=top_k)
        if not self.gate.passes(hits):
            # 불변식 ③: 확신 없으면 회피 → 핸드오프
            return QueryResponse(answer=HANDOFF_MSG, handoff=True, sources=[])
        # TODO(P4): 승인된 매뉴얼을 질문에 맞게 다듬어 답(generator.rephrase).
        return QueryResponse(answer="(P4에서 구현)", handoff=False, sources=[])
