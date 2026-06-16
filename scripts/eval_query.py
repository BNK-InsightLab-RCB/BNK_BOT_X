"""측정③ 가시화 — 질문 → 검색·게이트·답변. 변별(경비 vs 예산) + 회피(도메인 밖)."""
from __future__ import annotations

from src.chat.gate import PrecisionGate
from src.chat.generator import Generator
from src.chat.retriever import Retriever
from src.chat.service import ChatService
from src.config import settings
from src.ingestion.embedder import Embedder
from src.ingestion.qdrant_store import QdrantStore

CASES = [
    ("경비집행내역 저장이 안돼요", "branch", "expense save 기대"),
    ("예산집행내역 등록이 안돼요", "branch", "budget save 기대 (근거리 중복 변별)"),
    ("경비 승인하려는데 안돼요", "branch", "expense approve 기대 (액션 변별)"),
    ("비밀번호 어떻게 바꿔요", "branch", "도메인 밖 → 핸드오프 기대 (회피)"),
]


def main() -> None:
    store = QdrantStore(
        settings.qdrant_url, settings.qdrant_collection_name,
        dim=settings.embedding_dim, api_key=settings.qdrant_api_key,
    )
    if not store.ping():
        print("Qdrant 미가동 — docker compose up -d")
        return
    embedder = Embedder(settings.embedding_model, dim=settings.embedding_dim)
    retriever = Retriever(embedder, store)
    svc = ChatService(retriever, PrecisionGate(), Generator(
        settings.llm_base_url, settings.llm_api_key, settings.llm_model, settings.llm_timeout_s
    ))

    for q, role, note in CASES:
        hits = retriever.retrieve(q, role=role, top_k=3)
        resp = svc.answer(q, role=role)
        print(f"\nQ: {q}   [{note}]")
        if hits:
            t = hits[0]
            print(f"  top: {t['payload']['manual_id']}  (dense={t['dense']:.2f}, lexical={t['lexical']:.2f})")
        print(f"  handoff={resp.handoff}")
        print(f"  answer: {resp.answer[:140].replace(chr(10), ' ')}")


if __name__ == "__main__":
    main()
