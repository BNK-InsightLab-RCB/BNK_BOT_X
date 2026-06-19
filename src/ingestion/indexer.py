"""P3 — 적재: 매뉴얼 → KURE 임베딩 → Qdrant 포인트(역할별).

매뉴얼 1개 → 2 포인트(role=branch는 branch_md, role=it는 it_md 임베딩).
질의 시 역할 안에서 검색되도록 payload에 role/screen/table 등 포함.
"""
from __future__ import annotations

from src.ingestion.embedder import Embedder
from src.ingestion.qdrant_store import QdrantStore
from src.models import Manual

ROLES = ("branch", "it")


def sparse_text_for_manual(manual: Manual, role: str) -> str:
    """식별자 검색용 lexical surface.

    dense embedding은 승인 매뉴얼 산문을 대상으로 하지만, sparse는 식별자 recall이 목적이다.
    따라서 payload/lineage/facts에 있는 구조 식별자까지 같이 색인한다.
    """
    failure_modes = manual.facts.get("failure_modes", [])
    failure_bits: list[str] = []
    for fm in failure_modes:
        if not isinstance(fm, dict):
            continue
        failure_bits += [
            str(fm.get("error_code") or ""),
            str(fm.get("condition") or ""),
            str(fm.get("cause") or ""),
        ]

    parts = [
        manual.body_for(role),
        manual.id,
        manual.screen_id,
        manual.screen_ko,
        manual.action,
        manual.manual_type,
        manual.api_path or "",
        " ".join(manual.table_en),
        " ".join(manual.table_ko),
        " ".join(manual.lineage_ref),
        " ".join(failure_bits),
    ]
    return " ".join(p for p in parts if p)


class Indexer:
    def __init__(self, store: QdrantStore, embedder: Embedder):
        self.store = store
        self.embedder = embedder

    def index_manuals(self, manuals: list[Manual]) -> int:
        from qdrant_client.models import PointStruct, SparseVector

        points = []
        for m in manuals:
            for role in ROLES:
                dense_vector = self.embedder.embed_one(m.body_for(role))
                sparse_vector = self.embedder.get_sparse_vector(sparse_text_for_manual(m, role))
                vectors = {"dense": dense_vector}
                if sparse_vector:
                    vectors["sparse"] = SparseVector(**sparse_vector)
                points.append(
                    PointStruct(
                        id=self.store.point_id(m.id, role),
                        vector=vectors,
                        payload=m.payload(role),
                    )
                )
        return self.store.upsert(points) if points else 0
