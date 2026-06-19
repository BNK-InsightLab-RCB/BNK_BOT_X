"""lineage 그래프 — 관련작업 연결 + 화면 roll-up (Qdrant·Qwen 불필요, 결정론)."""
from pathlib import Path

from src.ingestion.extractor import Extractor
from src.ingestion.graph_store import GraphStore
from src.ingestion.manual import ManualBuilder

SRC = Path(__file__).resolve().parent.parent / "examples" / "bank_sample"


def _graph(tmp_path):
    ops = Extractor().extract(SRC)
    manuals = [ManualBuilder().build(o, use_llm=False) for o in ops]
    g = GraphStore(tmp_path / "g.sqlite3")
    g.build_from_manuals(manuals)
    return g


def test_related_links_ops_sharing_table(tmp_path):
    g = _graph(tmp_path)
    rel = {r["manual_id"] for r in g.related("manual_expense_register_save")}
    # 경비 저장↔승인은 TB_EXPENSE_EXEC·selectExpense 공유 → 연결
    assert "manual_expense_approve_approve" in rel
    # 예산은 다른 테이블 → 연결 안 됨
    assert "manual_budget_register_save" not in rel


def test_screen_rollup(tmp_path):
    g = _graph(tmp_path)
    ms = {m["manual_id"] for m in g.manuals_for_screen("EXPENSE_REGISTER")}
    assert "manual_expense_register_save" in ms


def test_graph_count(tmp_path):
    g = _graph(tmp_path)
    assert g.count() == 3
