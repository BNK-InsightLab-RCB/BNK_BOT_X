"""검수·동결 — draft → approve → frozen + 감사 로그 (결정론)."""
import json
from dataclasses import asdict

from src.ingestion.review import approve, approve_all, list_status
from src.models import Manual


def _write(d, m):
    (d / f"{m.id}.json").write_text(json.dumps(asdict(m), ensure_ascii=False), encoding="utf-8")


def test_approve_sets_frozen_and_audit(tmp_path):
    d = tmp_path / "manuals"
    d.mkdir()
    _write(d, Manual(id="manual_x", screen_id="S", action="save", status="draft"))

    assert list_status(d)[0]["status"] == "draft"
    assert approve(d, "manual_x", "kim") is True

    s = list_status(d)[0]
    assert s["status"] == "frozen"
    assert s["reviewed_at"]  # 시각 기록
    # 감사 로그
    log = tmp_path / "review_log.jsonl"
    assert log.exists()
    entry = json.loads(log.read_text(encoding="utf-8").strip())
    assert entry["manual_id"] == "manual_x" and entry["by"] == "kim"


def test_approve_all(tmp_path):
    d = tmp_path / "manuals"
    d.mkdir()
    _write(d, Manual(id="a", screen_id="S", status="draft"))
    _write(d, Manual(id="b", screen_id="S", status="draft"))
    assert approve_all(d, "boss") == 2
    assert all(s["status"] == "frozen" for s in list_status(d))


def test_approve_missing(tmp_path):
    d = tmp_path / "manuals"
    d.mkdir()
    assert approve(d, "nope") is False
