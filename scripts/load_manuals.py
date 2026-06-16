"""P3 — data/manuals/*.json → Qdrant 적재 + 적재 확인(retrieve).

  docker compose up -d  먼저(Qdrant 6335).
  PYTHONPATH=. python scripts/load_manuals.py
"""
from __future__ import annotations

import json

from src.config import settings
from src.ingestion.embedder import Embedder
from src.ingestion.indexer import Indexer
from src.ingestion.qdrant_store import QdrantStore
from src.models import Manual


def main() -> None:
    files = sorted(settings.manuals_dir.glob("*.json"))
    if not files:
        print("data/manuals/ 가 비어 있음 — 먼저 build_manuals.py 실행")
        return
    manuals = [Manual.from_dict(json.loads(f.read_text(encoding="utf-8"))) for f in files]

    store = QdrantStore(
        settings.qdrant_url, settings.qdrant_collection_name,
        dim=settings.embedding_dim, api_key=settings.qdrant_api_key,
    )
    if not store.ping():
        print("Qdrant 미가동 — docker compose up -d 먼저")
        return
    store.ensure_collection()

    embedder = Embedder(settings.embedding_model, dim=settings.embedding_dim)
    n = Indexer(store, embedder).index_manuals(manuals)
    print(f"loaded {len(manuals)} manuals → {n} points; collection count = {store.count()}")

    print("\n=== 적재 확인: retrieve('경비집행내역 저장이 안돼요', role=branch) ===")
    hits = store.search(embedder.embed_one("경비집행내역 저장이 안돼요"), top_k=3, role="branch")
    for h in hits:
        p = h.payload
        print(f"  score={h.score:.3f}  {p['manual_id']}  ({p['screen_ko']} / {p['action']})")


if __name__ == "__main__":
    main()
