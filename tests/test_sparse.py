"""sparse 식별자 색인 — Qdrant 없이 결정론 검증."""

from src.ingestion.embedder import Embedder
from src.ingestion.indexer import sparse_text_for_manual
from src.models import Manual


def test_sparse_text_contains_structural_identifiers():
    manual = Manual(
        id="manual_expense_register_save",
        screen_id="EXPENSE_REGISTER",
        screen_ko="경비집행내역 등록",
        action="save",
        api_path="/api/expense/save",
        table_en=["TB_EXPENSE_EXEC"],
        table_ko=["경비집행내역"],
        it_md="ExpenseMapper.insertExpense 처리",
        facts={
            "failure_modes": [
                {
                    "error_code": "E_AUTH",
                    "condition": '!SecurityUtil.hasAuthority("EXPENSE_SAVE")',
                    "cause": "경비 저장 권한이 없습니다.",
                }
            ]
        },
        lineage_ref=[
            "EXPENSE_REGISTER",
            "/api/expense/save",
            "ExpenseService.saveExpense",
            "ExpenseMapper.insertExpense",
            "TB_EXPENSE_EXEC",
        ],
    )

    text = sparse_text_for_manual(manual, "it")

    assert "TB_EXPENSE_EXEC" in text
    assert "/api/expense/save" in text
    assert "ExpenseMapper.insertExpense" in text
    assert "E_AUTH" in text
    assert "EXPENSE_SAVE" in text


def test_sparse_vector_is_deterministic_for_identifiers():
    first = Embedder.get_sparse_vector("TB_EXPENSE_EXEC")
    second = Embedder.get_sparse_vector("TB_EXPENSE_EXEC")

    assert first == second
    assert first is not None
    assert len(first["indices"]) == len(first["values"])
    assert len(first["indices"]) > 0
