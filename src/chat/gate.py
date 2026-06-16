"""정밀도 게이트 — 점수 충분하면 답, 아니면 회피·핸드오프. P0 스텁(→ P4).

핵심 불변식 ③: 확신 없으면 답하지 않는다. P0에선 항상 회피(False).
"""
from __future__ import annotations


class PrecisionGate:
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def passes(self, hits: list) -> bool:
        # TODO(P4): top score >= threshold AND 화면/역할 일치.
        return False
