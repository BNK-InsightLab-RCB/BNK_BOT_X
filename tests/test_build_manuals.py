"""매뉴얼 빌드 출력 정리 — 후보에서 빠진 이전 생성물을 제거한다."""

from scripts.build_manuals import _remove_stale_outputs


def test_remove_stale_generated_manual_outputs(tmp_path):
    keep = [
        tmp_path / "manual_keep.json",
        tmp_path / "manual_keep.branch.md",
        tmp_path / "manual_keep.it.md",
    ]
    stale = [
        tmp_path / "manual_stale.json",
        tmp_path / "manual_stale.branch.md",
        tmp_path / "manual_stale.it.md",
    ]
    unrelated = tmp_path / "notes.json"
    for p in keep + stale + [unrelated]:
        p.write_text("x", encoding="utf-8")

    removed = _remove_stale_outputs(tmp_path, {"manual_keep"})

    assert removed == 3
    assert all(p.exists() for p in keep)
    assert not any(p.exists() for p in stale)
    assert unrelated.exists()
