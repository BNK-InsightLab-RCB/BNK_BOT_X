"""핸드오프 축적 — 로깅·조회·해소 (결정론, Qdrant 불필요)."""
from src.chat.handoff_store import HandoffStore


def test_log_list_resolve(tmp_path):
    s = HandoffStore(tmp_path / "h.sqlite3")
    i1 = s.log("비밀번호 변경", "branch")  # 도메인 밖(top 없음)
    s.log("휴가 신청은 어디서", "branch", top_manual_id="manual_x", top_score=0.41)  # 근거리 미스

    assert s.count() == 2
    assert s.count("open") == 2

    items = s.list()
    assert items[0]["question"] == "휴가 신청은 어디서"  # 최신 먼저
    assert items[1]["top_manual_id"] is None  # 도메인 밖은 top 없음

    assert s.resolve(i1) is True
    assert s.count("open") == 1
    assert s.count("resolved") == 1
    assert s.list(status="resolved")[0]["id"] == i1
