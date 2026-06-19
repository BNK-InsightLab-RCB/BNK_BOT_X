"""검수·동결 CLI.

  PYTHONPATH=. python scripts/review_manuals.py                 # 목록·상태
  PYTHONPATH=. python scripts/review_manuals.py --approve <id> --by 홍길동
  PYTHONPATH=. python scripts/review_manuals.py --approve-all --by 홍길동
"""
from __future__ import annotations

import argparse

from src.config import settings
from src.ingestion.review import approve, approve_all, list_status


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--approve", metavar="MANUAL_ID")
    ap.add_argument("--approve-all", action="store_true")
    ap.add_argument("--by", default="reviewer")
    args = ap.parse_args()

    d = settings.manuals_dir
    if args.approve_all:
        n = approve_all(d, args.by)
        print(f"approved(frozen): {n} manuals  by={args.by}")
    elif args.approve:
        ok = approve(d, args.approve, args.by)
        print(f"approve {args.approve}: {'OK(frozen)' if ok else 'NOT FOUND'}")

    print("\n=== 매뉴얼 상태 ===")
    for s in list_status(d):
        mark = "🟢" if s["status"] == "frozen" else "⚪"
        print(f"  {mark} [{s['status']}] {s['id']}  ({s['screen_ko']}/{s['action']})  검수={s['reviewed_at'] or '-'}")


if __name__ == "__main__":
    main()
