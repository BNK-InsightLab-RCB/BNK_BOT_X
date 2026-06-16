"""[관리자] 적재 트리거. P0: 동기 스텁 실행(P3에서 비동기 잡으로)."""
from __future__ import annotations

from fastapi import APIRouter

from src.ingestion.pipeline import IngestionPipeline

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/ingest")
def ingest() -> dict:
    # TODO(P3): 비동기 잡 + 상태 조회. 지금은 스텁 파이프라인을 그대로 실행.
    return IngestionPipeline().run()
