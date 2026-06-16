"""DDL 파서 — CREATE TABLE의 COMMENT에서 표기의미(table_ko/column_ko/코드값) 추출.

영문명 + 한글 설명이 COMMENT에 함께 있으므로 결정론적으로 한 번에 뽑힌다.
예: STATUS CHAR(1) COMMENT '상태(R:등록, A:승인, C:마감)' → 코드값 {R:등록, A:승인, C:마감}
"""
from __future__ import annotations

import re
from pathlib import Path

_NAME_RE = re.compile(r"CREATE\s+TABLE\s+(\w+)", re.IGNORECASE)
_TKO_RE = re.compile(r"\)\s*COMMENT\s*=\s*'([^']*)'", re.IGNORECASE)
_COL_RE = re.compile(r"^\s*(\w+)\s+[^\n]*?\bCOMMENT\s+'([^']*)'", re.IGNORECASE | re.MULTILINE)
_CODE_RE = re.compile(r"([A-Za-z0-9]+)\s*:\s*([^,)]+)")
_SKIP = {"PRIMARY", "KEY", "UNIQUE", "INDEX", "CONSTRAINT", "FOREIGN"}


def parse_ddl(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    out: list[dict] = []
    for block in re.split(r"(?i)(?=CREATE\s+TABLE)", text):
        name = _NAME_RE.search(block)
        if not name:
            continue
        tko = _TKO_RE.search(block)
        columns: dict[str, str] = {}
        code_values: dict[str, dict[str, str]] = {}
        for cm in _COL_RE.finditer(block):
            col = cm.group(1).upper()
            if col in _SKIP:
                continue
            comment = cm.group(2).strip()
            columns[col] = comment
            codes = {k: v.strip() for k, v in _CODE_RE.findall(comment)}
            if codes:
                code_values[col] = codes
        out.append(
            {
                "table_en": name.group(1).upper(),
                "table_ko": tko.group(1).strip() if tko else "",
                "columns": columns,
                "code_values": code_values,
                "path": str(path),
            }
        )
    return out
