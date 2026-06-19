"""챗 API DTO."""
from __future__ import annotations

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    role: str = Field(default="branch", pattern="^(branch|it)$")
    top_k: int = 5


class Source(BaseModel):
    manual_id: str
    screen_ko: str = ""
    action: str = ""
    score: float = 0.0


class QueryResponse(BaseModel):
    answer: str
    handoff: bool = False
    sources: list[Source] = []
    related: list[Source] = []  # lineage 그래프로 연결된 관련 작업(같은 테이블/매퍼/화면)
