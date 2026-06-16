"""lineage 저장소(SQLite). P0에서 스키마 초기화. 적재(P1)·확장 탐색(P4)은 이후.

BNK_Bot_S 프로토타입은 그래프를 만들고 미사용이었음 — 여기선 실제 탐색에 쓴다.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


class GraphStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS edges (
                    src       TEXT NOT NULL,
                    rel       TEXT NOT NULL,
                    dst       TEXT NOT NULL,
                    screen_id TEXT,
                    PRIMARY KEY (src, rel, dst)
                )
                """
            )

    def add_edge(self, src: str, rel: str, dst: str, screen_id: str | None = None) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO edges (src, rel, dst, screen_id) VALUES (?, ?, ?, ?)",
                (src, rel, dst, screen_id),
            )

    def neighbors(self, node: str) -> list[tuple[str, str, str]]:
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT src, rel, dst FROM edges WHERE src = ? OR dst = ?",
                (node, node),
            ).fetchall()
        return [(r[0], r[1], r[2]) for r in rows]
