"""P2 — 매뉴얼 생성 + 검수·동결. P0에선 스텁.

Qwen이 추출된 사실을 요약 → branch_md / it_md (숫자·조건은 코드에서 verbatim,
의도는 주석에서, 업무 라벨은 table_ko에서). 그 뒤 사람 검토 → 동결.
불변식: LLM은 "사실의 요약"이지 저작이 아니다.
"""
from __future__ import annotations

from src.models import ExtractedOperation, Manual


class ManualBuilder:
    def build(self, op: ExtractedOperation) -> Manual:
        # TODO(P2): 사실 → branch_md/it_md 생성(LLM 요약) + 숫자 보존 가드레일.
        raise NotImplementedError("manual generation: P2")
