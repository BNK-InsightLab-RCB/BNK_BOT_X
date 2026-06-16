"""측정② — 생성 매뉴얼이 사실을 보존하고 branch가 내부를 노출하지 않는가.

정적 경로(use_llm=False)로 결정론 검증 → Qwen 없이도 회귀.
"""
from pathlib import Path

from src.ingestion.extractor import Extractor
from src.ingestion.manual import ManualBuilder, is_branch_clean

SRC = Path(__file__).resolve().parent.parent / "examples" / "bank_sample"


def _manual():
    op = next(
        o for o in Extractor().extract(SRC) if o.action == "save" and o.screen_id == "EXPENSE_REGISTER"
    )
    return ManualBuilder().build(op, use_llm=False)


def test_branch_hides_internals():
    m = _manual()
    assert is_branch_clean(m.branch_md)
    for bad in ["TB_EXPENSE_EXEC", "/api/expense", "ExpenseService", "E_AUTH", "STATUS", "hasAuthority"]:
        assert bad not in m.branch_md


def test_branch_has_user_facing_causes():
    m = _manual()
    assert "권한" in m.branch_md
    assert "마감" in m.branch_md  # 코드값 C → 마감(업무 용어)
    assert "금액" in m.branch_md


def test_it_preserves_chain_and_conditions_verbatim():
    m = _manual()
    assert "/api/expense/save" in m.it_md
    assert "TB_EXPENSE_EXEC" in m.it_md
    assert 'hasAuthority("EXPENSE_SAVE")' in m.it_md  # 조건 verbatim
    assert "STATUS" in m.it_md  # 표기의미 노출(IT)


def test_manual_contract():
    m = _manual()
    assert m.id == "manual_expense_register_save"
    assert m.status == "draft"
    assert len(m.facts["failure_modes"]) == 3
    assert "경비집행내역" in m.table_ko
