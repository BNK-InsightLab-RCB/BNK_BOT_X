"""검수·동결·편집 — draft → approve → frozen, 편집 + 감사 로그 (결정론)."""
import json
from dataclasses import asdict

from src.ingestion.review import approve, approve_all, edit, list_status, read
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


def test_edit_updates_content_bumps_version_and_audits(tmp_path):
    d = tmp_path / "manuals"
    d.mkdir()
    _write(d, Manual(id="m", screen_id="S", action="save", branch_md="old", status="frozen", version=1))

    m = edit(d, "m", branch_md="new 안내", by="kim")
    assert m.branch_md == "new 안내"
    assert m.version == 2  # 버전업
    assert m.reviewed_by == "kim"
    assert read(d, "m").branch_md == "new 안내"  # 디스크 반영

    entries = [json.loads(x) for x in (tmp_path / "review_log.jsonl").read_text(encoding="utf-8").splitlines()]
    assert entries[-1]["action"] == "edit" and entries[-1]["by"] == "kim"


def test_edit_missing_returns_none(tmp_path):
    d = tmp_path / "manuals"
    d.mkdir()
    assert edit(d, "nope", branch_md="x") is None
