"""P5 — 슬라이스 측정 게이트(측정③ 자동 채점).

기대값 기반 pass/fail:
- 변별: 답 가능 질문이 *맞는 매뉴얼*을 top으로 두고 답하는가(handoff=False).
- 회피(양방향): 도메인 밖 질문은 handoff=True 인가.
- 누출: branch 답변에 내부 식별자가 없는가.
모두 통과하면 exit 0, 아니면 1. (검색·게이트는 결정론, Qwen 답문은 비결정 → 답문은 누출만 검사)
"""
from __future__ import annotations

import sys

from src.chat.gate import PrecisionGate
from src.chat.generator import Generator
from src.chat.retriever import Retriever
from src.chat.service import ChatService, _is_bad_generated_answer
from src.config import settings
from src.ingestion.embedder import Embedder
from src.ingestion.manual import is_branch_clean
from src.ingestion.qdrant_store import QdrantStore

CASES = [
    {
        "q": "경비집행내역 저장이 안돼요",
        "manual": "manual_expense_register_save",
        "handoff": False,
        "keywords": ("권한", "마감", "금액"),
    },
    {
        "q": "예산집행내역 등록이 안돼요",
        "manual": "manual_budget_register_save",
        "handoff": False,
        "keywords": ("권한", "한도"),
    },
    {
        "q": "경비 승인하려는데 안돼요",
        "manual": "manual_expense_approve_approve",
        "handoff": False,
        "keywords": ("권한", "등록"),
    },
    {"q": "비밀번호 어떻게 바꿔요", "manual": None, "handoff": True},
    {"q": "휴가 신청은 어디서 하나요", "manual": None, "handoff": True},
]


def main() -> int:
    store = QdrantStore(
        settings.qdrant_url, settings.qdrant_collection_name,
        dim=settings.embedding_dim, api_key=settings.qdrant_api_key,
    )
    if not store.ping():
        print("Qdrant 미가동 — docker compose up -d")
        return 2
    embedder = Embedder(settings.embedding_model, dim=settings.embedding_dim)
    retriever = Retriever(embedder, store)
    svc = ChatService(retriever, PrecisionGate(), Generator(
        settings.llm_base_url, settings.llm_api_key, settings.llm_model, settings.llm_timeout_s
    ))

    passed = 0
    for c in CASES:
        hits = retriever.retrieve(c["q"], role="branch", top_k=3)
        resp = svc.answer(c["q"], role="branch")
        reasons = []
        if resp.handoff != c["handoff"]:
            reasons.append(f"handoff={resp.handoff}!={c['handoff']}")
        if not c["handoff"]:
            top = hits[0]["payload"]["manual_id"] if hits else None
            if top != c["manual"]:
                reasons.append(f"top={top}!={c['manual']}")
            if not is_branch_clean(resp.answer):
                reasons.append("branch leak")
            if _is_bad_generated_answer(resp.answer):
                reasons.append("bad generated answer")
            missing = [kw for kw in c.get("keywords", ()) if kw not in resp.answer]
            if missing:
                reasons.append(f"missing keywords={missing}")
        ok = not reasons
        passed += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {c['q']}" + (f"  ({'; '.join(reasons)})" if reasons else ""))

    total = len(CASES)
    print(f"\n측정③ 게이트: {passed}/{total} {'PASS ✅' if passed == total else 'FAIL ❌'}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
