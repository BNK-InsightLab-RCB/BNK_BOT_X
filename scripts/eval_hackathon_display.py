"""00.BNK_Hackathon 표시/의미 매뉴얼 실험 평가.

전제:
  DISPLAY_DIR=$(mktemp -d /private/tmp/bnkbotx-display-manuals.XXXXXX)
  SOURCE_DIR=/Users/jhyeong/Project/BNK/00.BNK_Hackathon MANUALS_DIR=$DISPLAY_DIR PYTHONPATH=. .venv/bin/python scripts/build_manuals.py --no-llm --freeze --include-display
  MANUALS_DIR=$DISPLAY_DIR QDRANT_COLLECTION_NAME=bnk_ops_knowledge_display_test PYTHONPATH=. .venv/bin/python scripts/load_manuals.py --recreate
  MANUALS_DIR=$DISPLAY_DIR QDRANT_COLLECTION_NAME=bnk_ops_knowledge_display_test PYTHONPATH=. .venv/bin/python scripts/eval_hackathon_display.py

평가 범위:
- failure-only 기본 경로를 건드리지 않고, --include-display 옵션에서만 조회/표시 항목 의미 질문을 답할 수 있어야 한다.
- "안돼요/오류/안보여요" 질문은 display 매뉴얼로 답하지 않고, failure 매뉴얼이 없으면 handoff 되어야 한다.
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


EXPECTED_MANUAL_COUNT = 34
EXPECTED_DISPLAY_MANUALS = {
    "manual_loan_execute_getHistory_display",
    "manual_loan_execute_getProducts_display",
    "manual_deposit_open_getAccounts_display",
    "manual_forex_transfer_getRates_display",
    "manual_receipt_print_searchReceipts_display",
}
EXPECTED_FAILURE_MANUALS = {
    "manual_loan_execute_executeLoan",
    "manual_deposit_open_openAccount",
}


CASES = [
    {
        "q": "대출 실행 이력 화면의 상태는 무슨 뜻이야",
        "manual": "manual_loan_execute_getHistory_display",
        "handoff": False,
        "keywords": ("정상", "연체", "상환완료"),
    },
    {
        "q": "대출 상품 목록의 금리 기준은 뭐야",
        "manual": "manual_loan_execute_getProducts_display",
        "handoff": False,
        "keywords": ("최저금리", "최고금리", "기준금리"),
    },
    {
        "q": "예금 계좌 목록의 만기처리방법은 무슨 뜻이야",
        "manual": "manual_deposit_open_getAccounts_display",
        "handoff": False,
        "keywords": ("자동해지", "자동갱신", "통보후처리"),
    },
    {
        "q": "외화 환율 화면의 매매기준율은 뭐야",
        "manual": "manual_forex_transfer_getRates_display",
        "handoff": False,
        "keywords": ("매매기준율",),
    },
    {
        "q": "장표 목록의 출력 상태는 무슨 뜻이야",
        "manual": "manual_receipt_print_searchReceipts_display",
        "handoff": False,
        "keywords": ("출력완료", "취소", "재출력"),
    },
    {
        "q": "대출 실행이 안돼요",
        "manual": "manual_loan_execute_executeLoan",
        "handoff": False,
        "keywords": ("고객번호", "대출상품", "금리", "대출금액"),
    },
    {
        "q": "고객 대출 실행 이력 조회하는데 조회가 안돼",
        "manual": None,
        "handoff": True,
    },
    {
        "q": "대출 상품 목록이 안보여요",
        "manual": None,
        "handoff": True,
    },
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
    if len(loaded_ids) != EXPECTED_MANUAL_COUNT:
        errors.append(f"manual count={len(loaded_ids)}, expected={EXPECTED_MANUAL_COUNT}")
    missing_display = sorted(EXPECTED_DISPLAY_MANUALS - loaded_ids)
    if missing_display:
        errors.append(f"missing display manuals: {missing_display}")
    missing_failure = sorted(EXPECTED_FAILURE_MANUALS - loaded_ids)
    if missing_failure:
        errors.append(f"missing failure manuals: {missing_failure}")

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
        print("Hackathon display 매뉴얼 적재 상태가 평가 전제와 다릅니다.")
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
    print(f"\nHackathon display 질의 게이트: {passed}/{total} {'PASS' if passed == total else 'FAIL'}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
