"""정밀도 게이트 — 점수 충분하면 답, 아니면 회피·핸드오프.

핵심 불변식 ③: 확신 없으면 답하지 않는다.
dense(의미) 또는 lexical(표기) 중 하나라도 절대 임계를 넘으면 통과. 둘 다 낮으면 회피.
"""
from __future__ import annotations


class PrecisionGate:
    def __init__(
        self,
        t_dense_high: float = 0.58,
        t_dense_low: float = 0.50,
        t_lexical: float = 0.40,
        t_lexical_support: float = 0.15,
    ):
        self.t_dense_high = t_dense_high
        self.t_dense_low = t_dense_low
        self.t_lexical = t_lexical
        self.t_lexical_support = t_lexical_support

    def passes(self, hits: list[dict]) -> bool:
        """강한 의미매칭(dense) 또는 강한 표기매칭(lexical) 단독 통과.
        borderline 의미(0.50~0.58)는 표기 뒷받침을 요구 → 도메인 무매칭 오답을 회피로 보낸다.
        """
        if not hits:
            return False
        if hits[0].get("manual_type_intent") and not hits[0].get("manual_type_match"):
            return False
        if hits[0].get("collection_intent") and not hits[0].get("collection_match"):
            return False
        if hits[0].get("action_intent") and not hits[0].get("action_match"):
            return False
        d, lx = hits[0]["dense"], hits[0]["lexical"]
        return (
            d >= self.t_dense_high
            or lx >= self.t_lexical
            or (d >= self.t_dense_low and lx >= self.t_lexical_support)
        )
