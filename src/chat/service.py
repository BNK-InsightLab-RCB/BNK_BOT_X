"""RAG 오케스트레이션: 검색 → 정밀도 게이트 → (충분)다듬기 / (부족)핸드오프.

불변식 ②: 질의 타임 LLM은 *검색된 매뉴얼 안에서만* 다듬는다(저작 금지).
Qwen 미가동/누출/부실 출력 시 승인 매뉴얼 기반 결정론 답변으로 폴백한다.
"""
from __future__ import annotations

import re

from src.chat.generator import GeneratorError
from src.chat.schemas import QueryResponse, Source
from src.ingestion.manual import is_branch_clean

HANDOFF_MSG = (
    "현재 확실히 답할 수 있는 근거(검수된 매뉴얼)를 찾지 못했습니다. "
    "담당 개발자에게 문의해 주세요."
)

_SYS_BRANCH = (
    "너는 은행 영업점 담당자를 돕는다. 아래 '매뉴얼'은 검색 게이트를 통과한 관련 매뉴얼이다. "
    "매뉴얼 안의 가능한 원인과 확인 사항만 질문에 맞게 간결히 안내하라. "
    "매뉴얼 밖의 새 사실·숫자·조치를 만들지 마라. "
    "소스코드·테이블명·API·내부 코드값·메서드명은 절대 쓰지 마라. "
    "매뉴얼이 비어 있거나 질문과 명백히 무관할 때만 모른다고 하라."
)
_SYS_IT = (
    "너는 IT 담당자를 돕는다. 아래 '매뉴얼'은 검색 게이트를 통과한 관련 매뉴얼이다. "
    "매뉴얼 안의 처리 흐름·조건만 사용해 질문에 답하라. "
    "매뉴얼 밖의 새 사실·숫자·조치를 만들지 마라. 처리 흐름·조건은 정확히 유지."
)

_BAD_GENERATED_PHRASES = (
    "(관리자 수정)",
    "제공된 매뉴얼에는",
    "관련된 구체적인 내용",
    "포함되어 있지 않습니다",
    "안내해 드릴 수 없습니다",
    "안내할 수 없습니다",
    "답변할 수 없습니다",
    "정보가 없습니다",
    "찾지 못했습니다",
    "확인할 수 없습니다",
)
_PLACEHOLDER_RE = re.compile(r"(^|\s|\n)[-*\d.]*\s*\.{3,}\s*($|\n)")


def _is_bad_generated_answer(answer: str) -> bool:
    text = (answer or "").strip()
    if not text:
        return True
    return any(phrase in text for phrase in _BAD_GENERATED_PHRASES) or bool(_PLACEHOLDER_RE.search(text))


def _extract_branch_fallback(body: str) -> str:
    """승인된 branch 매뉴얼에서 사용자 안내에 필요한 부분만 결정론적으로 추린다."""
    lines = [line.rstrip() for line in (body or "").splitlines()]
    intro = ""
    causes: list[str] = []
    closing = ""
    section = ""

    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            section = line
            continue
        if not intro and not section:
            intro = line
        elif section == "## 가능한 원인과 확인 사항" and re.match(r"^\d+\.\s+", line):
            causes.append(line)
        elif section == "## 그래도 안 되면" and not closing:
            closing = line

    if not causes:
        return body

    out = []
    if intro:
        out += [intro, ""]
    out += ["확인할 사항은 다음과 같습니다.", ""]
    out += causes
    if closing:
        out += ["", closing]
    return "\n".join(out)


def _fallback_answer(body: str, role: str) -> str:
    return _extract_branch_fallback(body) if role == "branch" else body


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
                if _is_bad_generated_answer(out):
                    return _fallback_answer(body, role)
                if role == "branch" and not is_branch_clean(out):
                    return _fallback_answer(body, role)  # 누출 위험 → 승인 매뉴얼 기반 폴백
                return out.strip()
        except GeneratorError:
            pass
        return _fallback_answer(body, role)  # Qwen 미가동 → 승인 매뉴얼 기반 폴백
