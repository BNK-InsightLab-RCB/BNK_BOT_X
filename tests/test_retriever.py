"""검색 랭킹 보조 신호 — 일반 업무 액션 의도만 반영한다."""

from src.chat.retriever import (
    _action_bonus,
    _action_match,
    _collection_bonus,
    _collection_match,
    _manual_type_bonus,
    _manual_type_match,
)


def test_action_bonus_matches_generic_business_action_intent():
    payload = {
        "action": "openAccount",
        "api_path": "/api/deposit/open",
        "screen_ko": "예금개설",
        "screen_id": "DEPOSIT_OPEN",
    }

    assert _action_bonus("예금 개설이 안돼요", payload) == 0.20


def test_action_bonus_does_not_match_different_action_intent():
    payload = {
        "action": "approve",
        "api_path": "/api/expense/approve",
        "screen_ko": "경비집행내역 승인",
        "screen_id": "EXPENSE_APPROVE",
    }

    assert _action_bonus("경비집행내역 저장이 안돼요", payload) == 0.0


def test_action_match_marks_explicit_intent_mismatch():
    payload = {
        "action": "openAccount",
        "api_path": "/api/deposit/open",
        "screen_ko": "예금개설",
        "screen_id": "DEPOSIT_OPEN",
    }

    assert _action_match("예금 상품 목록이 안보여요", payload) == (True, False)


def test_collection_match_rejects_history_query_against_customer_lookup():
    payload = {
        "action": "getCustomer",
        "api_path": "/api/customer/{custNo}",
        "screen_ko": "대출실행",
        "screen_id": "LOAN_EXECUTE",
    }

    assert _collection_match("고객 대출 실행 이력 조회하는데 조회가 안돼", payload) == (
        True,
        False,
    )


def test_collection_match_accepts_history_target():
    payload = {
        "action": "getHistory",
        "api_path": "/api/loan/history",
        "screen_ko": "대출실행",
        "screen_id": "LOAN_EXECUTE",
    }

    assert _collection_match("고객 대출 실행 이력 조회하는데 조회가 안돼", payload) == (
        True,
        True,
    )


def test_collection_match_keeps_history_queries_away_from_product_lists():
    payload = {
        "action": "getProducts",
        "api_path": "/api/loan/products",
        "screen_ko": "대출실행",
        "screen_id": "LOAN_EXECUTE",
    }

    assert _collection_match("대출 실행 이력 화면의 상태는 무슨 뜻이야", payload) == (
        True,
        False,
    )


def test_collection_match_accepts_product_list_when_query_mentions_product():
    payload = {
        "action": "getProducts",
        "api_path": "/api/loan/products",
        "screen_ko": "대출실행",
        "screen_id": "LOAN_EXECUTE",
    }

    assert _collection_match("대출 상품 목록의 금리 기준은 뭐야", payload) == (True, True)
    assert _collection_bonus("대출 상품 목록의 금리 기준은 뭐야", payload) == 0.15


def test_manual_type_match_routes_display_meaning_questions_to_display_manuals():
    assert _manual_type_match("대출 실행 이력 상태가 무슨 뜻이야", {"manual_type": "display"}) == (
        True,
        True,
    )
    assert _manual_type_match("대출 실행 이력 상태가 무슨 뜻이야", {"manual_type": "failure"}) == (
        True,
        False,
    )


def test_manual_type_match_routes_failure_questions_to_failure_manuals():
    assert _manual_type_match("대출 실행이 안돼요", {"manual_type": "failure"}) == (True, True)
    assert _manual_type_match("대출 실행이 안돼요", {"manual_type": "display"}) == (True, False)


def test_manual_type_bonus_promotes_matching_manual_family_only():
    assert _manual_type_bonus("대출 실행 이력 상태가 무슨 뜻이야", {"manual_type": "display"}) == 0.25
    assert _manual_type_bonus("대출 실행 이력 상태가 무슨 뜻이야", {"manual_type": "failure"}) == 0.0
    assert _manual_type_bonus("대출 실행 관련 안내", {"manual_type": "display"}) == 0.0
