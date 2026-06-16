"""[고객/담당자] 질의 라우터 — 얇은 컨트롤러. ChatService에 위임."""
from __future__ import annotations

from fastapi import APIRouter, Request

from src.chat.schemas import QueryRequest, QueryResponse

router = APIRouter(tags=["chat"])


@router.post("/query", response_model=QueryResponse)
def query(req: QueryRequest, request: Request) -> QueryResponse:
    service = request.app.state.chat_service
    return service.answer(req.question, role=req.role, top_k=req.top_k)
