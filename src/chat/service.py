"""RAG 오케스트레이션: 검색 → 정밀도 게이트 → (충분)다듬기 / (부족)핸드오프.

불변식 ②: 질의 타임 LLM은 *검색된 매뉴얼 안에서만* 다듬는다(저작 금지).
Qwen 미가동/누출 시 매뉴얼 원문을 그대로 반환(폴백). branch는 누출 검사 후 통과.
"""
from __future__ import annotations

from src.chat.generator import GeneratorError
from src.chat.schemas import QueryResponse, Source
from src.ingestion.manual import is_branch_clean

HANDOFF_MSG = (
    "현재 확실히 답할 수 있는 근거(검수된 매뉴얼)를 찾지 못했습니다. "
    "담당 개발자에게 문의해 주세요."
)

_SYS_BRANCH = (
    "너는 은행 영업점 담당자를 돕는다. 아래 '매뉴얼' 내용만으로 질문에 답하라. "
    "매뉴얼에 없으면 모른다고 하라. 소스코드·테이블명·API·내부 코드값·메서드명은 절대 쓰지 마라. "
    "간결한 한국어 안내만."
)
_SYS_IT = (
    "너는 IT 담당자를 돕는다. 아래 '매뉴얼' 내용만으로 질문에 답하라. "
    "매뉴얼에 없으면 모른다고 하라. 처리 흐름·조건은 정확히 유지."
)


class ChatService:
    def __init__(self, retriever, gate, generator, graph=None, handoffs=None):
        self.retriever = retriever
        self.gate = gate
        self.generator = generator
        self.graph = graph  # lineage 그래프(질의시점 관련작업 확장)
        self.handoffs = handoffs  # 핸드오프 축적

    def answer(self, question: str, role: str = "branch", top_k: int = 5) -> QueryResponse:
        hits = self.retriever.retrieve(question, role=role, top_k=top_k)
        if not self.gate.passes(hits):
            if self.handoffs is not None:  # 못 푼 질문 축적(빈틈 데이터)
                top = hits[0] if hits else None
                self.handoffs.log(
                    question, role,
                    top_manual_id=(top["payload"]["manual_id"] if top else None),
                    top_score=(round(float(top["score"]), 3) if top else None),
                )
            return QueryResponse(answer=HANDOFF_MSG, handoff=True, sources=[])
        top = hits[0]["payload"]
        answer = self._compose(question, top.get("body", ""), role)
        sources = [
            Source(
                manual_id=h["payload"]["manual_id"],
                screen_ko=h["payload"].get("screen_ko", ""),
                action=h["payload"].get("action", ""),
                score=round(float(h["score"]), 3),
            )
            for h in hits[:3]
        ]
        related = []
        if self.graph is not None:
            related = [
                Source(manual_id=r["manual_id"], screen_ko=r["screen_ko"], action=r["action"])
                for r in self.graph.related(top["manual_id"])
            ]
        return QueryResponse(answer=answer, handoff=False, sources=sources, related=related)

    def _compose(self, question: str, body: str, role: str) -> str:
        system = _SYS_BRANCH if role == "branch" else _SYS_IT
        user = f"[질문]\n{question}\n\n[매뉴얼]\n{body}"
        try:
            out = self.generator.rephrase(system, user)
            if out and out.strip():
                if role == "branch" and not is_branch_clean(out):
                    return body  # 누출 위험 → 승인 매뉴얼 원문 폴백
                return out.strip()
        except GeneratorError:
            pass
        return body  # Qwen 미가동 → 매뉴얼 원문 그대로
