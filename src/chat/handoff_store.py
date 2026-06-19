"""핸드오프 축적 — 회피(못 푼) 질문을 로깅·축적.

정밀도-우선 설계의 마지막 고리: 못 푼 질문 → 축적 → (사람 검토) 다음 빌드 매뉴얼 보강.
top_score가 임계 *바로 아래*면 "근거리 미스"(매뉴얼은 있는데 검색/임계 문제),
top이 없으면 "도메인 밖"(매뉴얼 부재) — 어디를 메울지 단서가 된다.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_COLS = ["id", "ts", "question", "role", "top_manual_id", "top_score", "status"]


class HandoffStore:
    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _init(self) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS handoffs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts TEXT, question TEXT, role TEXT,
                    top_manual_id TEXT, top_score REAL,
                    status TEXT DEFAULT 'open'
                )"""
            )

    def log(self, question: str, role: str = "branch", top_manual_id=None, top_score=None) -> int:
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute(
                "INSERT INTO handoffs (ts, question, role, top_manual_id, top_score) VALUES (?,?,?,?,?)",
                (
                    datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    question, role, top_manual_id, top_score,
                ),
            )
            return cur.lastrowid

    def list(self, status: str | None = None, limit: int = 100) -> list[dict]:
        query = "SELECT id, ts, question, role, top_manual_id, top_score, status FROM handoffs"
        args: list = []
        if status:
            query += " WHERE status = ?"
            args.append(status)
        query += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        with sqlite3.connect(self.path) as conn:
            rows = conn.execute(query, args).fetchall()
        return [dict(zip(_COLS, r)) for r in rows]

    def count(self, status: str | None = None) -> int:
        query = "SELECT COUNT(*) FROM handoffs"
        args: list = []
        if status:
            query += " WHERE status = ?"
            args.append(status)
        with sqlite3.connect(self.path) as conn:
            return conn.execute(query, args).fetchone()[0]

    def resolve(self, handoff_id: int) -> bool:
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute("UPDATE handoffs SET status='resolved' WHERE id = ?", (handoff_id,))
            return cur.rowcount > 0
