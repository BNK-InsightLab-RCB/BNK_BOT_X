"""00.BNK_Hackathon 전체 질의 회귀 평가.

전제:
  SOURCE_DIR=/Users/jhyeong/Project/BNK/00.BNK_Hackathon PYTHONPATH=. .venv/bin/python scripts/build_manuals.py --no-llm --freeze
  PYTHONPATH=. .venv/bin/python scripts/load_manuals.py --recreate

평가 범위:
- 주요 업무 오류 질문은 맞는 Hackathon failure 매뉴얼을 top으로 두고 답변 가능해야 한다.
- 조회/목록/이력처럼 매뉴얼 후보에서 제외된 질문과 도메인 밖 질문은 handoff 되어야 한다.
- 답변은 LLM 대신 승인 매뉴얼 기반 결정론 fallback으로 생성해 검색/게이트 회귀만 안정적으로 본다.
--include-display 적재 상태에서도 필수 failure 매뉴얼 회귀를 그대로 확인할 수 있다.
"""
from __future__ import annotations

import json
import sys

from src.chat.gate import PrecisionGate
from src.chat.generator import GeneratorError
from src.chat.retriever import Retriever
from src.chat.service import ChatService, _is_bad_generated_answer
from src.config import settings
from src.ingestion.embedder import Embedder
from src.ingestion.manual import is_branch_clean
from src.ingestion.qdrant_store import QdrantStore
from src.models import Manual


EXPECTED_MANUALS = {
    "manual_accounting_voucher_createVoucher",
    "manual_bancassurance_subscribe_calculatePremium",
    "manual_bancassurance_subscribe_getCustomer",
    "manual_bancassurance_subscribe_subscribe",
    "manual_bill_discount_executeDiscount",
    "manual_bill_discount_getBill",
    "manual_card_issue_getCustomer",
    "manual_card_issue_issueCard",
    "manual_check_issue_issueCheck",
    "manual_deposit_open_getCustomer",
    "manual_deposit_open_openAccount",
    "manual_forex_transfer_executeTransfer",
    "manual_loan_execute_executeLoan",
    "manual_loan_execute_getCustomer",
    "manual_receipt_print_getDetail",
}


CASES = [
    {
        "q": "대출 실행이 안돼요",
        "manual": "manual_loan_execute_executeLoan",
        "handoff": False,
        "keywords": ("고객번호", "대출상품", "금리", "대출금액"),
    },
    {
        "q": "예금 개설이 안돼요",
        "manual": "manual_deposit_open_openAccount",
        "handoff": False,
        "keywords": ("고객번호", "예금상품", "최소 입금액"),
    },
    {
        "q": "카드 발급이 안돼요",
        "manual": "manual_card_issue_issueCard",
        "handoff": False,
        "keywords": ("고객번호", "카드상품", "체크카드", "신용등급"),
    },
    {
        "q": "전표 입력이 안돼요",
        "manual": "manual_accounting_voucher_createVoucher",
        "handoff": False,
        "keywords": ("차변", "대변", "0원"),
    },
    {
        "q": "수표 발행이 안돼요",
        "manual": "manual_check_issue_issueCheck",
        "handoff": False,
        "keywords": ("10만원", "단위"),
    },
    {
        "q": "외화 송금이 안돼요",
        "manual": "manual_forex_transfer_executeTransfer",
        "handoff": False,
        "keywords": ("환율",),
    },
    {
        "q": "어음 할인이 안돼요",
        "manual": "manual_bill_discount_executeDiscount",
        "handoff": False,
        "keywords": ("어음번호", "할인 불가능", "만기일"),
    },
    {
        "q": "보험 가입이 안돼요",
        "manual": "manual_bancassurance_subscribe_subscribe",
        "handoff": False,
        "keywords": ("고객번호", "보험상품"),
    },
    {
        "q": "보험료 계산이 안돼요",
        "manual": "manual_bancassurance_subscribe_calculatePremium",
        "handoff": False,
        "keywords": ("보험상품",),
    },
    {
        "q": "장표 상세 조회가 안돼요",
        "manual": "manual_receipt_print_getDetail",
        "handoff": False,
        "keywords": ("장표번호",),
    },
    {
        "q": "고객 대출 실행 이력 조회하는데 조회가 안돼",
        "manual": None,
        "handoff": True,
    },
    {"q": "대출 상품 목록이 안보여요", "manual": None, "handoff": True},
    {"q": "예금 상품 목록이 안보여요", "manual": None, "handoff": True},
    {"q": "해외계좌 거래내역 조회가 안돼요", "manual": None, "handoff": True},
    {"q": "비밀번호 변경은 어디서 해요", "manual": None, "handoff": True},
    {"q": "휴가 신청은 어디서 하나요", "manual": None, "handoff": True},
]


class DeterministicFallbackGenerator:
    def rephrase(self, system: str, user: str) -> str:  # noqa: ARG002
        raise GeneratorError("deterministic eval: use approved manual fallback")


def _loaded_manual_ids() -> set[str]:
    ids: set[str] = set()
    for f in settings.manuals_dir.glob("*.json"):
        manual = Manual.from_dict(json.loads(f.read_text(encoding="utf-8")))
        if manual.status == "frozen":
            ids.add(manual.id)
    return ids


def _preflight(store: QdrantStore) -> list[str]:
    errors: list[str] = []
    loaded_ids = _loaded_manual_ids()
    missing = sorted(EXPECTED_MANUALS - loaded_ids)
    if missing:
        errors.append(f"missing Hackathon manuals in data/manuals: {missing}")
    count = store.count()
    expected_points = len(loaded_ids) * 2
    if count != expected_points:
        errors.append(f"qdrant point count={count}, expected={expected_points}")
    return errors


def main() -> int:
    store = QdrantStore(
        settings.qdrant_url,
        settings.qdrant_collection_name,
        dim=settings.embedding_dim,
        api_key=settings.qdrant_api_key,
    )
    if not store.ping():
        print("Qdrant 미가동 — docker compose up -d")
        return 2

    preflight_errors = _preflight(store)
    if preflight_errors:
        print("Hackathon 매뉴얼 적재 상태가 평가 전제와 다릅니다.")
        for err in preflight_errors:
            print(f"  - {err}")
        return 2

    embedder = Embedder(settings.embedding_model, dim=settings.embedding_dim)
    retriever = Retriever(embedder, store)
    svc = ChatService(retriever, PrecisionGate(), DeterministicFallbackGenerator())

    passed = 0
    for case in CASES:
        hits = retriever.retrieve(case["q"], role="branch", top_k=3)
        resp = svc.answer(case["q"], role="branch", top_k=3)
        top = hits[0]["payload"]["manual_id"] if hits else None
        reasons: list[str] = []

        if resp.handoff != case["handoff"]:
            reasons.append(f"handoff={resp.handoff}!={case['handoff']}")
        if case["manual"] and top != case["manual"]:
            reasons.append(f"top={top}!={case['manual']}")
        if not case["handoff"]:
            if not is_branch_clean(resp.answer):
                reasons.append("branch leak")
            if _is_bad_generated_answer(resp.answer):
                reasons.append("bad generated answer")
            missing_keywords = [kw for kw in case.get("keywords", ()) if kw not in resp.answer]
            if missing_keywords:
                reasons.append(f"missing keywords={missing_keywords}")
        elif resp.sources:
            reasons.append("handoff response should not expose sources")

        ok = not reasons
        passed += ok
        score = hits[0]["score"] if hits else 0.0
        print(
            f"  [{'PASS' if ok else 'FAIL'}] {case['q']} "
            f"(top={top}, score={score:.3f}, handoff={resp.handoff})"
            + (f"  {'; '.join(reasons)}" if reasons else "")
        )

    total = len(CASES)
    print(f"\nHackathon 질의 게이트: {passed}/{total} {'PASS ✅' if passed == total else 'FAIL ❌'}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
