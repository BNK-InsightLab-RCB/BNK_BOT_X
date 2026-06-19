"""검수·동결·편집 — 매뉴얼은 draft로 생성, 사람이 검토·수정 후 승인하면 frozen.

설계의 "검수·동결 = 감사 가능성" 실체화:
- 적재(load)는 frozen만 → draft는 사용자에게 안 닿는다.
- 승인/편집 시 검수자·시각 기록 + `review_log.jsonl` 감사 로그.
- 편집은 frozen 유지 + version+1(관리자=신뢰된 검수자). 본문 변경분은 호출부에서 재적재.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from src.models import Manual


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _path(manuals_dir: Path | str, manual_id: str) -> Path:
    return Path(manuals_dir) / f"{manual_id}.json"


def read(manuals_dir: Path | str, manual_id: str) -> Manual | None:
    f = _path(manuals_dir, manual_id)
    if not f.exists():
        return None
    return Manual.from_dict(json.loads(f.read_text(encoding="utf-8")))


def _write(manuals_dir: Path | str, manual: Manual) -> None:
    _path(manuals_dir, manual.id).write_text(
        json.dumps(asdict(manual), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _audit(manuals_dir: Path | str, manual_id: str, action: str, by: str, ts: str) -> None:
    log = Path(manuals_dir).parent / "review_log.jsonl"
    with log.open("a", encoding="utf-8") as fh:
        fh.write(
            json.dumps({"ts": ts, "manual_id": manual_id, "action": action, "by": by}, ensure_ascii=False)
            + "\n"
        )


def list_status(manuals_dir: Path | str) -> list[dict]:
    out = []
    for f in sorted(Path(manuals_dir).glob("*.json")):
        m = Manual.from_dict(json.loads(f.read_text(encoding="utf-8")))
        out.append(
            {"id": m.id, "status": m.status, "version": m.version, "reviewed_at": m.reviewed_at,
             "screen_ko": m.screen_ko, "action": m.action}
        )
    return out


def approve(manuals_dir: Path | str, manual_id: str, reviewer: str = "reviewer") -> bool:
    m = read(manuals_dir, manual_id)
    if m is None:
        return False
    ts = _now()
    m.status = "frozen"
    m.reviewed_at = ts
    m.reviewed_by = reviewer
    _write(manuals_dir, m)
    _audit(manuals_dir, manual_id, "approve", reviewer, ts)
    return True


def approve_all(manuals_dir: Path | str, reviewer: str = "reviewer") -> int:
    n = 0
    for s in list_status(manuals_dir):
        if s["status"] != "frozen" and approve(manuals_dir, s["id"], reviewer):
            n += 1
    return n


def edit(
    manuals_dir: Path | str,
    manual_id: str,
    branch_md: str | None = None,
    it_md: str | None = None,
    by: str = "reviewer",
) -> Manual | None:
    """관리자 매뉴얼 본문 수정 → version+1 + 감사. (frozen 유지; 재적재는 호출부)"""
    m = read(manuals_dir, manual_id)
    if m is None:
        return None
    if branch_md is not None:
        m.branch_md = branch_md
    if it_md is not None:
        m.it_md = it_md
    m.version += 1
    ts = _now()
    m.reviewed_at = ts
    m.reviewed_by = by
    _write(manuals_dir, m)
    _audit(manuals_dir, manual_id, "edit", by, ts)
    return m
