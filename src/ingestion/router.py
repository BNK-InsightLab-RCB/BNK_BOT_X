"""[관리자] 적재 · 핸드오프 · 매뉴얼 편집."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from src.config import settings
from src.ingestion.indexer import Indexer
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.review import approve, edit, list_status, read

router = APIRouter(prefix="/admin", tags=["admin"])


class ManualEdit(BaseModel):
    branch_md: str | None = None
    it_md: str | None = None
    by: str = "reviewer"


# ---- 적재 -----------------------------------------------------------------
@router.post("/ingest")
def ingest() -> dict:
    # TODO: 비동기 잡 + 상태 조회. 지금은 스텁 파이프라인을 그대로 실행.
    return IngestionPipeline().run()


# ---- 핸드오프 -------------------------------------------------------------
@router.get("/handoffs")
def handoffs(request: Request, status: str | None = None) -> dict:
    store = request.app.state.handoffs
    return {"open": store.count("open"), "total": store.count(), "items": store.list(status=status)}


@router.post("/handoffs/{handoff_id}/resolve")
def resolve_handoff(handoff_id: int, request: Request) -> dict:
    ok = request.app.state.handoffs.resolve(handoff_id)
    return {"resolved": ok, "id": handoff_id}


# ---- 매뉴얼 (관리자 편집) -------------------------------------------------
def _reindex(request: Request, manual) -> bool:
    """frozen 매뉴얼만 Qdrant에 재적재(편집/승인 결과를 라이브 반영)."""
    store = getattr(request.app.state, "store", None)
    if manual is None or manual.status != "frozen" or store is None:
        return False
    Indexer(store, request.app.state.embedder).index_manuals([manual])
    return True


@router.get("/manuals")
def list_manuals() -> dict:
    return {"items": list_status(settings.manuals_dir)}


@router.get("/manuals/{manual_id}")
def get_manual(manual_id: str) -> dict:
    m = read(settings.manuals_dir, manual_id)
    if m is None:
        raise HTTPException(status_code=404, detail="manual not found")
    return m.to_dict()


@router.put("/manuals/{manual_id}")
def edit_manual(manual_id: str, body: ManualEdit, request: Request) -> dict:
    m = edit(settings.manuals_dir, manual_id, branch_md=body.branch_md, it_md=body.it_md, by=body.by)
    if m is None:
        raise HTTPException(status_code=404, detail="manual not found")
    return {
        "id": m.id, "version": m.version, "status": m.status,
        "reviewed_at": m.reviewed_at, "reviewed_by": m.reviewed_by,
        "reindexed": _reindex(request, m),
    }


@router.post("/manuals/{manual_id}/approve")
def approve_manual(manual_id: str, request: Request, by: str = "reviewer") -> dict:
    if not approve(settings.manuals_dir, manual_id, by):
        raise HTTPException(status_code=404, detail="manual not found")
    m = read(settings.manuals_dir, manual_id)
    return {"id": manual_id, "status": "frozen", "reindexed": _reindex(request, m)}
