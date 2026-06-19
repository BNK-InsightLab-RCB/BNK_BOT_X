"""lineage 그래프(SQLite) — 매뉴얼의 lineage 노드를 저장해 *질의시점 확장*에 쓴다.

- 관련 작업: 같은 노드(테이블·매퍼·API·화면)를 공유하는 다른 매뉴얼 (교차 화면 연결)
- 화면 roll-up: 한 화면에 속한 오퍼레이션 매뉴얼들

BNK_Bot_S는 그래프를 만들고 *안 썼다* — 여기선 실제 검색 확장에 쓴다(그 함정을 피함).
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from src.models import Manual


def _node_type(node: str) -> str:
    if node.startswith("TB_"):
        return "table"
    if node.startswith("/"):
        return "api"
    if "." in node:
        return "method"
    return "screen"


class GraphStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS manual_meta (
                    manual_id TEXT PRIMARY KEY, screen_id TEXT, screen_ko TEXT, action TEXT
                )"""
            )
            conn.execute(
                """CREATE TABLE IF NOT EXISTS manual_nodes (
                    manual_id TEXT, node TEXT, ntype TEXT, PRIMARY KEY (manual_id, node)
                )"""
            )
            conn.execute("CREATE INDEX IF NOT EXISTS ix_mn_node ON manual_nodes(node)")

    def reset(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute("DELETE FROM manual_meta")
            conn.execute("DELETE FROM manual_nodes")

    def build_from_manuals(self, manuals: Iterable[Manual]) -> int:
        self.reset()
        meta, nodes = [], []
        for m in manuals:
            meta.append((m.id, m.screen_id, m.screen_ko, m.action))
            node_set = set(m.lineage_ref) | set(m.table_en) | {m.screen_id}
            if m.api_path:
                node_set.add(m.api_path)
            for n in node_set:
                if n:
                    nodes.append((m.id, n, _node_type(n)))
        with sqlite3.connect(self.path) as conn:
            conn.executemany("INSERT OR REPLACE INTO manual_meta VALUES (?,?,?,?)", meta)
            conn.executemany("INSERT OR REPLACE INTO manual_nodes VALUES (?,?,?)", nodes)
        return len(meta)

    def count(self) -> int:
        with sqlite3.connect(self.path) as conn:
            return conn.execute("SELECT COUNT(*) FROM manual_meta").fetchone()[0]

    def manuals_for_screen(self, screen_id: str) -> list[dict]:
        """화면 roll-up — 한 화면에 속한 모든 오퍼레이션 매뉴얼."""
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                "SELECT manual_id, screen_ko, action FROM manual_meta WHERE screen_id = ?",
                (screen_id,),
            ).fetchall()
        return [{"manual_id": r[0], "screen_ko": r[1], "action": r[2]} for r in rows]

    def related(self, manual_id: str, limit: int = 5) -> list[dict]:
        """같은 lineage 노드를 공유하는 다른 매뉴얼(공유 노드 많은 순)."""
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(
                """
                SELECT mn2.manual_id, mm.screen_ko, mm.action,
                       GROUP_CONCAT(DISTINCT mn2.node) AS shared
                FROM manual_nodes mn1
                JOIN manual_nodes mn2
                     ON mn1.node = mn2.node AND mn2.manual_id != mn1.manual_id
                JOIN manual_meta mm ON mm.manual_id = mn2.manual_id
                WHERE mn1.manual_id = ?
                GROUP BY mn2.manual_id, mm.screen_ko, mm.action
                ORDER BY COUNT(DISTINCT mn2.node) DESC
                LIMIT ?
                """,
                (manual_id, limit),
            ).fetchall()
        return [
            {"manual_id": r[0], "screen_ko": r[1], "action": r[2], "shared": (r[3] or "").split(",")}
            for r in rows
        ]
