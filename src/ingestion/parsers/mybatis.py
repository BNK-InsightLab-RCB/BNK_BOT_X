"""MyBatis XML 파서 — SQL id → 테이블 + 앞선 한글 주석.

서비스의 mapper 호출(예: ExpenseMapper.insertExpense)을 테이블로 연결하는 다리.
"""
from __future__ import annotations

import re
from pathlib import Path

_NS_RE = re.compile(r'<mapper\s+namespace="([^"]+)"', re.IGNORECASE)
_STMT_RE = re.compile(
    r'<(select|insert|update|delete)\s+id="(\w+)"[^>]*>(.*?)</\1>', re.DOTALL | re.IGNORECASE
)
_TABLE_RE = re.compile(r"\b(?:FROM|INTO|UPDATE|JOIN)\s+(\w+)", re.IGNORECASE)
_COMMENT_RE = re.compile(r"<!--\s*(.*?)\s*-->", re.DOTALL)


def parse_mybatis(path: Path) -> dict[str, dict]:
    text = path.read_text(encoding="utf-8")
    ns = _NS_RE.search(text)
    namespace = ns.group(1) if ns else path.stem
    simple = namespace.split(".")[-1]
    out: dict[str, dict] = {}
    for m in _STMT_RE.finditer(text):
        crud, sid, inner = m.group(1).upper(), m.group(2), m.group(3)
        tables: list[str] = []
        for t in _TABLE_RE.findall(inner):
            tu = t.upper()
            if tu not in tables:
                tables.append(tu)
        before = _COMMENT_RE.findall(text[: m.start()])
        out[f"{simple}.{sid}"] = {
            "sql_id": f"{namespace}.{sid}",
            "crud": crud,
            "tables": tables,
            "comment": before[-1].strip() if before else "",
            "path": str(path),
        }
    return out
