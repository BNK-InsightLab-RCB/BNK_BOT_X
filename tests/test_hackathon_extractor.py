"""P6 — 00.BNK_Hackathon 현실형 샘플 파서 일반화 게이트."""

from pathlib import Path

import pytest

from src.ingestion.extractor import Extractor
from src.ingestion.manual import manual_candidates

SRC = Path(__file__).resolve().parents[2] / "00.BNK_Hackathon"


def _ops():
    if not SRC.exists():
        pytest.skip("00.BNK_Hackathon sibling sample is not available")
    return Extractor().extract(SRC)


def _loan_execute():
    matches = [
        op
        for op in _ops()
        if op.screen_id == "LOAN_EXECUTE" and op.api_path == "/api/loan/execute"
    ]
    assert len(matches) == 1
    return matches[0]


def test_hackathon_react_service_layer_extracts_operations():
    ops = _ops()
    assert len(ops) >= 30
    apis = {op.api_path for op in ops}
    assert "/api/loan/execute" in apis
    assert "/api/deposit/open" in apis
    assert "/api/card/issue" in apis


def test_hackathon_actions_prefer_frontend_api_function_names():
    ops = _ops()
    assert not [op.action for op in ops if "{" in op.action or "}" in op.action]

    customers = [op for op in ops if op.api_path == "/api/customer/{custNo}"]
    assert customers
    assert {op.action for op in customers} == {"getCustomer"}

    deposit_open = next(op for op in ops if op.api_path == "/api/deposit/open")
    assert deposit_open.action == "openAccount"


def test_hackathon_manual_candidates_drop_zero_failure_lookup_ops():
    candidates = manual_candidates(_ops())
    apis = {op.api_path for op in candidates}

    assert candidates
    assert all(op.failure_modes for op in candidates)
    assert "/api/deposit/open" in apis
    assert "/api/loan/execute" in apis
    assert "/api/accounting/voucher" in apis

    assert "/api/deposit/products" not in apis
    assert "/api/loan/products" not in apis
    assert "/api/forex/rates" not in apis
    assert "/api/receipt/templates" not in apis


def test_hackathon_loan_execute_lineage():
    op = _loan_execute()
    assert op.screen_ko == "대출실행"
    assert "LoanService.executeLoan" in op.lineage
    assert "CustomerMapper.findByCustNo" in op.lineage
    assert "LoanMapper.findProductByCd" in op.lineage
    assert "LoanMapper.insertLoanExec" in op.lineage
    assert {"TB_CUSTOMER", "TB_LOAN_PRODUCT", "TB_LOAN_EXEC"} <= set(op.table_en)


def test_hackathon_illegal_argument_failures_and_multiline_if():
    op = _loan_execute()
    messages = {fm.cause: fm.condition for fm in op.failure_modes}

    assert "고객번호가 존재하지 않습니다." in messages
    assert messages["고객번호가 존재하지 않습니다."] == "cust == null"
    assert "대출상품이 존재하지 않습니다." in messages
    assert "적용금리가 허용 범위를 벗어났습니다." in messages
    assert (
        messages["적용금리가 허용 범위를 벗어났습니다."]
        == "req.getInterestRate().compareTo(product.getMinRate()) < 0 || "
        "req.getInterestRate().compareTo(product.getMaxRate()) > 0"
    )
    assert "대출금액이 허용 범위를 벗어났습니다." in messages
