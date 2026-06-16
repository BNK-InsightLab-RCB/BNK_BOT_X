"""프론트 파서 — 화면 식별/이름 + API 호출(axios).

화면(screen_id, screen_ko)을 api_path에 연결해 오퍼레이션의 시작점을 만든다.
"""
from __future__ import annotations

import re
from pathlib import Path

_SCREEN_RE = re.compile(r"""screenId\s*:\s*["']([^"']+)["']""")
_H1_RE = re.compile(r"<h1[^>]*>(.*?)</h1>", re.DOTALL | re.IGNORECASE)
_AXIOS_RE = re.compile(
    r"""axios\.(get|post|put|patch|delete)\s*\(\s*["']([^"']+)["']""", re.IGNORECASE
)


def parse_frontend(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    sid = _SCREEN_RE.search(text)
    h1 = _H1_RE.search(text)
    screen_ko = re.sub(r"<[^>]+>", "", h1.group(1)).strip() if h1 else ""
    calls: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for m in _AXIOS_RE.finditer(text):
        key = (m.group(1).upper(), m.group(2))
        if key not in seen:
            seen.add(key)
            calls.append({"http_method": m.group(1).upper(), "api_path": m.group(2)})
    return {
        "screen_id": sid.group(1) if sid else "",
        "screen_ko": screen_ko,
        "api_calls": calls,
        "path": str(path),
    }
