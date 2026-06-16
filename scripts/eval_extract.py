"""측정① 가시화 — 추출된 오퍼레이션을 사람이 읽기 좋게 출력."""
from __future__ import annotations

from pathlib import Path

from src.config import settings
from src.ingestion.extractor import Extractor


def main() -> None:
    ops = Extractor().extract(settings.source_dir)
    print(f"operations extracted: {len(ops)}\n")
    for op in ops:
        print(f"■ {op.screen_ko} ({op.screen_id}) · action={op.action}")
        print(f"  lineage : {' → '.join(op.lineage)}")
        print(f"  tables  : {', '.join(f'{e}({k})' for e, k in zip(op.table_en, op.table_ko))}")
        print(f"  failure modes ({len(op.failure_modes)}):")
        for fm in op.failure_modes:
            print(f"    - [{fm.error_code}] {fm.cause}")
            print(f"        조건: {fm.condition}")
            print(f"        의미(주석): {fm.meaning}")
        for tbl, n in op.notation.items():
            print(f"  표기의미 {tbl}: code_values={n['code_values']}")
        print()


if __name__ == "__main__":
    main()
