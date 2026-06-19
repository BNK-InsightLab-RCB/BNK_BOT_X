"""FastAPI 엔진 진입점.

P0: 골격이 부팅되고 `/health`가 Qdrant readiness를 본다. 로직은 스텁.
싱글톤(embedder/store/generator/chat_service)은 lifespan에서 1회 구성.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.chat.gate import PrecisionGate
from src.chat.generator import Generator
from src.chat.handoff_store import HandoffStore
from src.chat.retriever import Retriever
from src.chat.router import router as chat_router
from src.chat.service import ChatService
from src.config import settings
from src.ingestion.embedder import Embedder
from src.ingestion.graph_store import GraphStore
from src.ingestion.qdrant_store import QdrantStore
from src.ingestion.router import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    embedder = Embedder(settings.embedding_model, dim=settings.embedding_dim)

    store: QdrantStore | None
    try:
        store = QdrantStore(
            settings.qdrant_url,
            settings.qdrant_collection_name,
            dim=settings.embedding_dim,
            api_key=settings.qdrant_api_key,
        )
        if store.ping():
            store.ensure_collection()
        else:
            store = None  # Qdrant 미가동: 골격은 떠도 /health는 degraded/down
    except Exception:
        store = None

    generator = Generator(
        settings.llm_base_url, settings.llm_api_key, settings.llm_model, settings.llm_timeout_s
    )
    retriever = Retriever(embedder, store)
    gate = PrecisionGate()
    graph = GraphStore(settings.graph_db_path)
    handoffs = HandoffStore(settings.handoff_db_path)

    app.state.embedder = embedder
    app.state.store = store
    app.state.generator = generator
    app.state.graph = graph
    app.state.handoffs = handoffs
    app.state.chat_service = ChatService(retriever, gate, generator, graph, handoffs)
    yield


app = FastAPI(
    title="BNK_BOT_X — Source-Aware Ops Support Engine",
    version="0.0.1-p0",
    lifespan=lifespan,
)
app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/health")
def health():
    """Readiness: Qdrant 연결 + 포인트 확인."""
    store = getattr(app.state, "store", None)
    if store is None or not store.ping():
        return JSONResponse(
            status_code=503, content={"status": "down", "reason": "qdrant unreachable"}
        )
    n = store.count()
    return {
        "status": "ok" if n > 0 else "degraded",
        "points": n,
        "collection": settings.qdrant_collection_name,
    }
