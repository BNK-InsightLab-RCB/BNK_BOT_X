"""[관리자] 적재 트리거. P0: 동기 스텁 실행(P3에서 비동기 잡으로)."""
from __future__ import annotations

from fastapi import APIRouter, Request

from src.ingestion.pipeline import IngestionPipeline

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/ingest")
def ingest() -> dict:
    # TODO(P3): 비동기 잡 + 상태 조회. 지금은 스텁 파이프라인을 그대로 실행.
    return IngestionPipeline().run()


@router.get("/handoffs")
def handoffs(request: Request, status: str | None = None) -> dict:
    """축적된 핸드오프(못 푼 질문) — '어디에 매뉴얼이 비었나' 데이터."""
    store = request.app.state.handoffs
    return {"open": store.count("open"), "total": store.count(), "items": store.list(status=status)}


@router.post("/handoffs/{handoff_id}/resolve")
def resolve_handoff(handoff_id: int, request: Request) -> dict:
    """매뉴얼 보강으로 해소된 핸드오프 표시."""
    ok = request.app.state.handoffs.resolve(handoff_id)
    return {"resolved": ok, "id": handoff_id}
