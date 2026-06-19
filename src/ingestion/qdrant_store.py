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


def _has_named(config: Any, name: str) -> bool:
    return isinstance(config, dict) and name in config


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
        else:
            self._validate_collection_schema()
        for field_name in INDEXED_FIELDS:  # idempotent
            try:
                self.client.create_payload_index(
                    self.collection,
                    field_name=field_name,
                    field_schema=PayloadSchemaType.KEYWORD,
                )
            except Exception:
                pass

    def _validate_collection_schema(self) -> None:
        info = self.client.get_collection(self.collection)
        params = info.config.params
        vectors = getattr(params, "vectors", None)
        sparse_vectors = getattr(params, "sparse_vectors", None)
        dense = vectors.get("dense") if _has_named(vectors, "dense") else None
        dense_size = getattr(dense, "size", None)
        if dense_size != self.dim or not _has_named(sparse_vectors, "sparse"):
            raise RuntimeError(
                f"Qdrant collection '{self.collection}' schema mismatch. "
                "Run scripts/load_manuals.py --recreate to rebuild dense+sparse vectors."
            )

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
        self.client.upsert(self.collection, points=points)
        return len(points)

    def search(
        self,
        query: list[float] | dict,
        top_k: int = 5,
        role: str | None = None,
        using: str = "dense",
    ):
        """dense 또는 sparse named vector 검색."""
        from qdrant_client.models import FieldCondition, Filter, MatchValue, SparseVector

        flt = None
        if role:
            flt = Filter(must=[FieldCondition(key="role", match=MatchValue(value=self.nfc(role)))])
        q = SparseVector(**query) if using == "sparse" and isinstance(query, dict) else query
        res = self.client.query_points(
            self.collection, query=q, using=using, limit=top_k,
            query_filter=flt, with_payload=True,
        )
        return res.points
