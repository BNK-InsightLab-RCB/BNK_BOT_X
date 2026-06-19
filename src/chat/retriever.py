"""질문 → 매뉴얼 검색(하이브리드: dense + Qdrant sparse, payload role 필터).

- dense: KURE 임베딩(미설치 시 해시 폴백) cosine.
- sparse: Qdrant native sparse vector. 한글 표기와 내부 식별자 exact-ish recall 보강.
- 둘을 합쳐 랭킹. 게이트는 dense/lexical의 *절대값*으로 회피를 판단(P4 gate).
"""
from __future__ import annotations


_ACTION_TERMS = {
    "save": ("save", "create", "register", "저장", "등록", "입력", "생성"),
    "approve": ("approve", "approval", "승인", "결재"),
    "open": ("open", "개설"),
    "issue": ("issue", "발급", "발행"),
    "execute": ("execute", "exec", "실행", "처리"),
    "subscribe": ("subscribe", "가입"),
    "transfer": ("transfer", "송금", "이체"),
    "discount": ("discount", "할인"),
    "calculate": ("calculate", "calc", "계산", "산출"),
    "get": ("get", "list", "search", "find", "조회", "검색", "상세", "목록"),
}
_COLLECTION_QUERY_TERMS = ("이력", "목록", "리스트", "내역 조회", "조회 내역", "history", "list")
_COLLECTION_TARGET_TERMS = (
    "history",
    "list",
    "search",
    "accounts",
    "vouchers",
    "transfers",
    "subscriptions",
    "receipts",
    "transactions",
    "이력",
    "목록",
)


def _action_families(text: str) -> set[str]:
    normalized = (text or "").lower()
    return {family for family, terms in _ACTION_TERMS.items() if any(t.lower() in normalized for t in terms)}


def _action_match(question: str, payload: dict) -> tuple[bool, bool]:
    query_families = _action_families(question)
    if not query_families:
        return False, False
    target = " ".join(
        str(payload.get(k) or "") for k in ("action", "api_path", "screen_ko", "screen_id")
    )
    return True, bool(query_families & _action_families(target))


def _action_bonus(question: str, payload: dict) -> float:
    _, matched = _action_match(question, payload)
    return 0.20 if matched else 0.0


def _collection_match(question: str, payload: dict) -> tuple[bool, bool]:
    q = (question or "").lower()
    has_intent = any(term.lower() in q for term in _COLLECTION_QUERY_TERMS)
    if not has_intent:
        return False, False
    target = " ".join(
        str(payload.get(k) or "").lower() for k in ("action", "api_path", "screen_ko", "screen_id")
    )
    return True, any(term.lower() in target for term in _COLLECTION_TARGET_TERMS)


class Retriever:
    def __init__(self, embedder, store):
        self.embedder = embedder
        self.store = store

    def retrieve(self, question: str, role: str = "branch", top_k: int = 5) -> list[dict]:
        if self.store is None:
            return []
        qvec = self.embedder.embed_one(question)
        raw_dense = self.store.search(qvec, top_k=max(top_k, 10), role=role, using="dense")

        q_sparse = self.embedder.get_sparse_vector(question)
        raw_sparse = []
        if q_sparse:
            try:
                raw_sparse = self.store.search(
                    q_sparse, top_k=max(top_k, 10), role=role, using="sparse"
                )
            except Exception:
                raw_sparse = []  # sparse 장애가 답변 경로 전체를 깨지 않도록 dense fallback

        hits_by_id: dict[str, dict] = {}
        for h in raw_dense:
            hits_by_id[str(h.id)] = {
                "payload": h.payload,
                "dense": max(float(h.score), 0.0),
                "sparse_score": 0.0,
            }
        for h in raw_sparse:
            key = str(h.id)
            if key not in hits_by_id:
                hits_by_id[key] = {"payload": h.payload, "dense": 0.0, "sparse_score": 0.0}
            hits_by_id[key]["sparse_score"] = max(float(h.score), 0.0)

        q_len = max(len(self.embedder.bigrams(question)), 1)
        hits: list[dict] = []
        for item in hits_by_id.values():
            lexical = min(item["sparse_score"] / q_len, 1.0)
            dense = item["dense"]
            action_intent, action_match = _action_match(question, item["payload"])
            collection_intent, collection_match = _collection_match(question, item["payload"])
            action_bonus = _action_bonus(question, item["payload"])
            hits.append(
                {
                    "payload": item["payload"],
                    "dense": dense,
                    "lexical": lexical,
                    "action_intent": action_intent,
                    "action_match": action_match,
                    "collection_intent": collection_intent,
                    "collection_match": collection_match,
                    "score": dense + lexical + action_bonus,
                }
            )
        hits.sort(key=lambda x: x["score"], reverse=True)
        return hits[:top_k]
