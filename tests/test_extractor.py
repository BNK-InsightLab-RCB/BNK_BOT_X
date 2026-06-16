"""측정① — Extractor가 슬라이스 화면의 체인을 정확히 뽑는가 (회귀 게이트)."""
from pathlib import Path

from src.ingestion.extractor import Extractor

SRC = Path(__file__).resolve().parent.parent / "examples" / "bank_sample"


def _save_op():
    ops = Extractor().extract(SRC)
    matches = [o for o in ops if o.screen_id == "EXPENSE_REGISTER" and o.action == "save"]
    assert len(matches) == 1, [(o.screen_id, o.action) for o in ops]
    return matches[0]


def test_lineage_chain():
    op = _save_op()
    assert op.screen_ko == "경비집행내역 등록"
    assert op.api_path == "/api/expense/save"
    assert "ExpenseService.saveExpense" in op.lineage
    assert "ExpenseMapper.insertExpense" in op.lineage
    assert "TB_EXPENSE_EXEC" in op.lineage


def test_notation_from_ddl_comment():
    op = _save_op()
    assert "TB_EXPENSE_EXEC" in op.table_en
    assert "경비집행내역" in op.table_ko
    codes = op.notation["TB_EXPENSE_EXEC"]["code_values"]
    assert codes["STATUS"]["C"] == "마감"
    assert codes["USE_YN"]["Y"] == "사용"


def test_failure_modes():
    op = _save_op()
    codes = {fm.error_code for fm in op.failure_modes}
    assert {"E_AUTH", "E_CLOSED", "E_AMOUNT"} <= codes
    auth = next(fm for fm in op.failure_modes if fm.error_code == "E_AUTH")
    assert "EXPENSE_SAVE" in auth.condition  # 코드 조건 verbatim
    assert "권한" in auth.meaning  # 한글 주석(업무 의도)


def test_korean_comments_captured():
    op = _save_op()
    joined = " ".join(op.comments)
    assert "마감" in joined
    assert "권한" in joined
