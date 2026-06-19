"""정밀도 게이트 — borderline 의미 매칭은 표기 뒷받침이 필요하다."""

from src.chat.gate import PrecisionGate


def _hit(dense: float, lexical: float) -> dict:
    return {"dense": dense, "lexical": lexical}


def test_gate_passes_strong_dense_or_lexical_match():
    gate = PrecisionGate()

    assert gate.passes([_hit(0.58, 0.0)])
    assert gate.passes([_hit(0.10, 0.40)])


def test_gate_requires_lexical_support_for_borderline_dense_match():
    gate = PrecisionGate()

    assert gate.passes([_hit(0.53, 0.15)])
    assert not gate.passes([_hit(0.53, 0.0)])
    assert not gate.passes([_hit(0.49, 0.39)])


def test_gate_rejects_top_hit_when_explicit_action_intent_mismatches():
    gate = PrecisionGate()

    hit = {
        "dense": 0.74,
        "lexical": 0.42,
        "action_intent": True,
        "action_match": False,
    }

    assert not gate.passes([hit])


def test_gate_rejects_collection_query_when_top_hit_is_not_collection_lookup():
    gate = PrecisionGate()

    hit = {
        "dense": 0.75,
        "lexical": 0.37,
        "collection_intent": True,
        "collection_match": False,
        "action_intent": True,
        "action_match": True,
    }

    assert not gate.passes([hit])


def test_gate_rejects_manual_type_mismatch_before_score_thresholds():
    gate = PrecisionGate()

    hit = {
        "dense": 0.75,
        "lexical": 0.45,
        "manual_type_intent": True,
        "manual_type_match": False,
    }

    assert not gate.passes([hit])
