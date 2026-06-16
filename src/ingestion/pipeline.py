"""빌드 타임 배치: 소스 → 추출 → 매뉴얼 생성 → (검수·동결) → 임베딩 → 적재.

P0: 스텁 배선만(추출 0건, 매뉴얼 0건). 단계 채우기는 P1~P3.
"""
from __future__ import annotations

from pathlib import Path

from src.config import settings
from src.ingestion.extractor import Extractor
from src.ingestion.manual import ManualBuilder


class IngestionPipeline:
    def __init__(self) -> None:
        self.extractor = Extractor()
        self.manual = ManualBuilder()

    def run(self, source_dir: Path | str | None = None) -> dict:
        source_dir = Path(source_dir or settings.source_dir)
        operations = self.extractor.extract(source_dir)
        # TODO(P2/P3): 매뉴얼 생성 → 검수·동결 → 임베딩 → Qdrant + 그래프.
        return {
            "source_dir": str(source_dir),
            "operations_found": len(operations),
            "manuals_built": 0,
            "status": "skeleton",
        }
