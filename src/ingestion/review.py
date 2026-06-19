"""검수·동결 — 매뉴얼은 draft로 생성, 사람이 검토 후 승인하면 frozen.

설계의 "검수·동결 = 감사 가능성" 실체화:
- 적재(load)는 frozen만 → draft는 사용자에게 안 닿는다.
- 승인 시 검수자·시각 기록 + `review_log.jsonl` 감사 로그.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from src.models import Manual


def list_status(manuals_dir: Path | str) -> list[dict]:
    out = []
    for f in sorted(Path(manuals_dir).glob("*.json")):
        m = Manual.from_dict(json.loads(f.read_text(encoding="utf-8")))
        out.append(
            {"id": m.id, "status": m.status, "reviewed_at": m.reviewed_at,
             "screen_ko": m.screen_ko, "action": m.action}
        )
    return out


def approve(manuals_dir: Path | str, manual_id: str, reviewer: str = "reviewer") -> bool:
    manuals_dir = Path(manuals_dir)
    f = manuals_dir / f"{manual_id}.json"
    if not f.exists():
        return False
    m = Manual.from_dict(json.loads(f.read_text(encoding="utf-8")))
    m.status = "frozen"
    m.reviewed_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    m.reviewed_by = reviewer
    f.write_text(json.dumps(asdict(m), ensure_ascii=False, indent=2), encoding="utf-8")
    log = manuals_dir.parent / "review_log.jsonl"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(
            {"ts": m.reviewed_at, "manual_id": manual_id, "action": "approve", "by": reviewer},
            ensure_ascii=False,
        ) + "\n")
    return True


def approve_all(manuals_dir: Path | str, reviewer: str = "reviewer") -> int:
    n = 0
    for s in list_status(manuals_dir):
        if s["status"] != "frozen" and approve(manuals_dir, s["id"], reviewer):
            n += 1
    return n
