"""식별자 검색 게이트 — sparse 검색 품질 자동 채점.

자연어 질의는 eval_answer.py가 본다. 이 스크립트는 테이블/API/Mapper/error code처럼
dense embedding만으로 흔들리는 식별자 질의가 올바른 매뉴얼을 top으로 두는지 확인한다.

  docker compose up -d
  PYTHONPATH=. python scripts/load_manuals.py --recreate
  PYTHONPATH=. python scripts/eval_identifier.py
"""
from __future__ import annotations

import sys

from src.chat.retriever import Retriever
from src.config import settings
from src.ingestion.embedder import Embedder
from src.ingestion.qdrant_store import QdrantStore

CASES = [
    {
        "q": "TB_EXPENSE_EXEC",
        "role": "it",
        "manuals": {"manual_expense_register_save", "manual_expense_approve_approve"},
    },
    {"q": "TB_BUDGET_EXEC", "role": "it", "manuals": {"manual_budget_register_save"}},
    {"q": "/api/expense/save", "role": "it", "manuals": {"manual_expense_register_save"}},
    {"q": "/api/budget/save", "role": "it", "manuals": {"manual_budget_register_save"}},
    {
        "q": "ExpenseMapper.insertExpense",
        "role": "it",
        "manuals": {"manual_expense_register_save"},
    },
    {
        "q": "ExpenseMapper.updateStatus",
        "role": "it",
        "manuals": {"manual_expense_approve_approve"},
    },
    {"q": "E_LIMIT", "role": "it", "manuals": {"manual_budget_register_save"}},
    {"q": "E_STATUS", "role": "it", "manuals": {"manual_expense_approve_approve"}},
    {"q": "EXPENSE_SAVE", "role": "it", "manuals": {"manual_expense_register_save"}},
    {"q": "EXPENSE_APPROVE", "role": "it", "manuals": {"manual_expense_approve_approve"}},
]


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

    retriever = Retriever(Embedder(settings.embedding_model, dim=settings.embedding_dim), store)
    passed = 0
    for case in CASES:
        hits = retriever.retrieve(case["q"], role=case["role"], top_k=3)
        top = hits[0] if hits else None
        top_manual = top["payload"]["manual_id"] if top else None
        lexical = float(top["lexical"]) if top else 0.0
        reasons = []
        if top_manual not in case["manuals"]:
            reasons.append(f"top={top_manual}!={sorted(case['manuals'])}")
        if lexical < 0.40:
            reasons.append(f"lexical={lexical:.2f}<0.40")
        ok = not reasons
        passed += ok
        print(
            f"  [{'PASS' if ok else 'FAIL'}] {case['q']} -> {top_manual} "
            f"(dense={(top['dense'] if top else 0):.2f}, lexical={lexical:.2f})"
            + (f"  ({'; '.join(reasons)})" if reasons else "")
        )

    total = len(CASES)
    print(f"\n식별자 검색 게이트: {passed}/{total} {'PASS' if passed == total else 'FAIL'}")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
