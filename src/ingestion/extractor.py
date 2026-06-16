"""P1 — Extractor (소스 → 구조화된 사실). P0에선 스텁.

DDL(+COMMENT)·Java·MyBatis·Vue를 파싱해 오퍼레이션(화면 × 액션 = 하나의 lineage
체인) 단위로 ExtractedOperation 생성: lineage + 표기의미(table_ko/column_ko/코드값)
+ 오류 + 코드 위치에 묶인 한글 주석.

이 프로젝트의 *가장 큰 리스크*. 측정① = 슬라이스 화면의 체인을 정확히 뽑는가.
"""
from __future__ import annotations

from pathlib import Path

from src.models import ExtractedOperation


class Extractor:
    def extract(self, source_dir: Path) -> list[ExtractedOperation]:
        # TODO(P1): 화면→API→Service→Mapper→WHERE→테이블 lineage,
        #           DDL COMMENT 표기의미, throw/조건 오류, 한글 주석(위치 묶음).
        return []
