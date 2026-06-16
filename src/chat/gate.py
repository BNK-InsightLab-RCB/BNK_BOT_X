"""정밀도 게이트 — 점수 충분하면 답, 아니면 회피·핸드오프.

핵심 불변식 ③: 확신 없으면 답하지 않는다.
dense(의미) 또는 lexical(표기) 중 하나라도 절대 임계를 넘으면 통과. 둘 다 낮으면 회피.
"""
from __future__ import annotations


class PrecisionGate:
    def __init__(self, t_dense: float = 0.50, t_lexical: float = 0.40):
        self.t_dense = t_dense
        self.t_lexical = t_lexical

    def passes(self, hits: list[dict]) -> bool:
        if not hits:
            return False
        top = hits[0]
        return top["dense"] >= self.t_dense or top["lexical"] >= self.t_lexical
