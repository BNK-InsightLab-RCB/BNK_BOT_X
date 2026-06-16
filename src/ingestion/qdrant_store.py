"""Qdrant 어댑터 — 단일 컬렉션, 하이브리드 대비(dense + sparse 명명 벡터).

새 코드(복사 아님). BNK_Bot의 *결정*만 계승:
- 단일 컬렉션 + payload 파티셔닝 + NFC 정규화 정확 필터.
- 결정론 point id(재적재가 중복 대신 덮어쓰기).
추가: dense('dense') + sparse('sparse') 명명 벡터로 하이브리드 검색 대비.

P0에선 ensure/ping/count만 쓴다. upsert(P3)·search(P4)는 골격 자리.
"""
from __future__ import annotations

import unicodedata
import uuid
from typing import Any

_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_DNS, "bnk_bot_x")
INDEXED_FIELDS = ("role", "screen_id", "action", "table_en")


class QdrantStore:
    def __init__(self, url: str, collection: str, dim: int = 1024, api_key: str | None = None):
        from qdrant_client import QdrantClient

        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection = collection
        self.dim = dim

    def ping(self) -> bool:
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False

    def ensure_collection(self, recreate: bool = False) -> None:
        from qdrant_client.models import (
            Distance,
            PayloadSchemaType,
            SparseVectorParams,
            VectorParams,
        )

        exists = self.client.collection_exists(self.collection)
        if exists and recreate:
            self.client.delete_collection(self.collection)
            exists = False
        if not exists:
            self.client.create_collection(
                self.collection,
                vectors_config={"dense": VectorParams(size=self.dim, distance=Distance.COSINE)},
                sparse_vectors_config={"sparse": SparseVectorParams()},
            )
        for field_name in INDEXED_FIELDS:  # idempotent
            try:
                self.client.create_payload_index(
                    self.collection,
                    field_name=field_name,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass

    def count(self) -> int:
        try:
            return self.client.count(self.collection, exact=True).count
        except Exception:
            return 0

    @staticmethod
    def point_id(manual_id: str, role: str) -> str:
        return str(uuid.uuid5(_NAMESPACE, f"{manual_id}:{role}"))

    @staticmethod
    def nfc(value: Any) -> Any:
        return unicodedata.normalize("NFC", value) if isinstance(value, str) else value

    def upsert(self, points: list) -> int:
        raise NotImplementedError("Qdrant upsert: P3")

    def search(self, *args, **kwargs):
        raise NotImplementedError("hybrid search: P4")
