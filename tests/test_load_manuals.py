"""매뉴얼 적재 전 품질 검증."""

from scripts.load_manuals import _invalid_manual_reasons
from src.models import Manual


def test_invalid_manual_reasons_reject_placeholder_branch_body():
    manual = Manual(
        id="manual_x",
        screen_id="S",
        branch_md="## (관리자 수정) 가능한 원인\n- ...",
        it_md="# IT",
        status="frozen",
    )

    assert "bad branch body" in _invalid_manual_reasons(manual)


def test_invalid_manual_reasons_accept_clean_branch_body():
    manual = Manual(
        id="manual_x",
        screen_id="S",
        branch_md="화면에서 처리가 안 되는 경우 권한과 상태를 확인해 주세요.",
        it_md="# IT",
        status="frozen",
    )

    assert _invalid_manual_reasons(manual) == []
