"""P3 — 적재: 매뉴얼 → KURE 임베딩 → Qdrant 포인트(역할별).

매뉴얼 1개 → 2 포인트(role=branch는 branch_md, role=it는 it_md 임베딩).
질의 시 역할 안에서 검색되도록 payload에 role/screen/table 등 포함.
"""
from __future__ import annotations

from src.ingestion.embedder import Embedder
from src.ingestion.qdrant_store import QdrantStore
from src.models import Manual

ROLES = ("branch", "it")


class Indexer:
    def __init__(self, store: QdrantStore, embedder: Embedder):
        self.store = store
        self.embedder = embedder

    def index_manuals(self, manuals: list[Manual]) -> int:
        from qdrant_client.models import PointStruct

        points = []
        for m in manuals:
            for role in ROLES:
                vector = self.embedder.embed_one(m.body_for(role))
                points.append(
                    PointStruct(
                        id=self.store.point_id(m.id, role),
                        vector={"dense": vector},
                        payload=m.payload(role),
                    )
                )
        return self.store.upsert(points) if points else 0
