"""P2 빌드 — 소스 → 매뉴얼 생성 → data/manuals/에 적재(+검수용 .md).

  PYTHONPATH=. python scripts/build_manuals.py            # Qwen 다듬기 시도
  PYTHONPATH=. python scripts/build_manuals.py --no-llm   # 정적만(결정론)
  PYTHONPATH=. python scripts/build_manuals.py --freeze    # 검수 통과로 동결
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict

from src.config import settings
from src.ingestion.extractor import Extractor
from src.ingestion.manual import ManualBuilder


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-llm", action="store_true", help="Qwen 없이 정적 생성")
    ap.add_argument("--freeze", action="store_true", help="status=frozen 으로 동결")
    args = ap.parse_args()

    ops = Extractor().extract(settings.source_dir)
    builder = ManualBuilder()
    out_dir = settings.manuals_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    for op in ops:
        m = builder.build(op, use_llm=not args.no_llm)
        if args.freeze:
            m.status = "frozen"
        (out_dir / f"{m.id}.json").write_text(
            json.dumps(asdict(m), ensure_ascii=False, indent=2), encoding="utf-8"
        )
        (out_dir / f"{m.id}.branch.md").write_text(m.branch_md, encoding="utf-8")
        (out_dir / f"{m.id}.it.md").write_text(m.it_md, encoding="utf-8")
        print(f"\n==================== {m.id} (status={m.status}) ====================")
        print("---------- branch_md ----------")
        print(m.branch_md)
        print("\n---------- it_md ----------")
        print(m.it_md)


if __name__ == "__main__":
    main()
