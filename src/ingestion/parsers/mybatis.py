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
_ALIAS_RE = re.compile(r"\b(?:FROM|JOIN)\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?", re.IGNORECASE)
_SELECT_RE = re.compile(r"\bSELECT\b(.*?)\bFROM\b", re.DOTALL | re.IGNORECASE)
_COMMENT_RE = re.compile(r"<!--\s*(.*?)\s*-->", re.DOTALL)
_SQL_KEYWORDS = {
    "AND",
    "CROSS",
    "FULL",
    "GROUP",
    "HAVING",
    "INNER",
    "JOIN",
    "LEFT",
    "LIMIT",
    "OFFSET",
    "ON",
    "ORDER",
    "OUTER",
    "RIGHT",
    "WHERE",
}


def _table_aliases(inner: str) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for table, alias in _ALIAS_RE.findall(inner):
        tu = table.upper()
        aliases[tu] = tu
        if alias and alias.upper() not in _SQL_KEYWORDS:
            aliases[alias.upper()] = tu
    return aliases


def _selected_columns(inner: str, crud: str) -> dict[str, list[str]]:
    if crud != "SELECT":
        return {}
    sm = _SELECT_RE.search(inner)
    if not sm:
        return {}
    aliases = _table_aliases(inner)
    tables = sorted(set(aliases.values()))

    out: dict[str, list[str]] = {}
    for raw in sm.group(1).split(","):
        expr = re.sub(r"\s+", " ", raw).strip()
        if not expr or "(" in expr:
            continue
        if expr.endswith(".*"):
            owner = expr[:-2].strip()
            table = aliases.get(owner.upper(), owner.upper())
            out.setdefault(table, [])
            continue
        if "*" in expr:
            continue
        expr = re.split(r"\s+AS\s+", expr, flags=re.IGNORECASE)[0].strip()
        expr = expr.split()[0]
        if "." in expr:
            owner, col = expr.split(".", 1)
            table = aliases.get(owner.upper(), owner.upper())
        else:
            table = tables[0] if len(tables) == 1 else ""
            col = expr
        col = re.sub(r"[^0-9A-Za-z_]", "", col).upper()
        if not col:
            continue
        key = table or "_UNKNOWN"
        out.setdefault(key, [])
        if col not in out[key]:
            out[key].append(col)
    return out


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
            "columns_by_table": _selected_columns(inner, crud),
            "comment": before[-1].strip() if before else "",
            "path": str(path),
        }
    return out
