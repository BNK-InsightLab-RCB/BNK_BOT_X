"""P2 — 매뉴얼 생성 + 검수·동결.

ExtractedOperation(사실) → branch_md / it_md.
- 결정론 우선: 정적 빌더가 사실에서 직접 매뉴얼을 만든다(숫자·조건 verbatim, 코드값 C→마감 조인).
- LLM(Qwen)은 *다듬기*만(같은 내용, 자연스러운 한국어). 실패/미가동이면 정적 결과가 그대로 매뉴얼.
- branch는 내부 식별자(테이블명·API·코드값·메서드)를 절대 노출하지 않는다(불변식 ②).
"""
from __future__ import annotations

import re
from dataclasses import asdict

from src.chat.generator import Generator, GeneratorError
from src.config import settings
from src.models import ExtractedOperation, Manual

# 내부 식별자 패턴(branch 노출 금지 + 차단 검증)
_TB = re.compile(r"\bTB_[A-Z0-9_]+\b")
_API = re.compile(r"/api/[\w/]+")
_ECODE = re.compile(r"\bE_[A-Z0-9_]+\b")
_METHOD = re.compile(r"\b[A-Z][A-Za-z0-9]+\.[A-Za-z0-9_]+\b")
_PAREN_ID = re.compile(r"\s*\([^)]*(?:[A-Z]{2,}|=)[^)]*\)")
_AUTH = re.compile(r"hasAuthority\([^)]*\)", re.IGNORECASE)
_INTERNAL = (_TB, _API, _ECODE, _METHOD)
_DISPLAY_ACTION_RE = re.compile(
    r"(?:^get|^search|list|history|products|accounts|templates|rates|transfers|subscriptions|transactions)",
    re.IGNORECASE,
)

BRANCH_SYS = (
    "너는 은행 영업점 담당자를 돕는 업무 안내 작성자다. 아래 초안과 *같은 내용*을 더 자연스러운 한국어로 다듬어라.\n"
    "규칙:\n"
    "1) 새 사실·숫자를 만들지 마라. 초안에 없는 내용 추가 금지.\n"
    "2) 소스코드·테이블명·API 경로·내부 코드값·메서드명·영문 식별자는 절대 쓰지 마라. 업무 용어로만.\n"
    "3) Markdown으로 출력. 매뉴얼 본문만(설명·머리말 없이)."
)
IT_SYS = (
    "너는 IT 담당자용 기술 매뉴얼을 다듬는다. 처리 흐름·실패 조건·표기의미를 정확히 유지하라.\n"
    "숫자·조건 코드는 그대로(verbatim) 둔다. Markdown 본문만 출력."
)


def _strip_internal(text: str) -> str:
    t = _PAREN_ID.sub("", text or "")
    t = _AUTH.sub("", t)
    for p in _INTERNAL:
        t = p.sub("", t)
    return re.sub(r"\s{2,}", " ", t).strip(" .·-")


def is_branch_clean(md: str) -> bool:
    """branch 본문에 내부 식별자가 없는지(불변식 ② 검증)."""
    md = md or ""
    return not any(p.search(md) for p in _INTERNAL) and "STATUS" not in md and "hasAuthority" not in md


def is_manual_candidate(op: ExtractedOperation) -> bool:
    """매뉴얼 생성 대상 여부.

    실패 조건이 없는 단순 조회/드롭다운 API는 정밀도 게이트의 노이즈가 되므로
    Extractor 원자료에는 남기되 사용자에게 적재되는 매뉴얼에서는 제외한다.
    """
    return bool(op.failure_modes)


def is_display_candidate(op: ExtractedOperation) -> bool:
    """화면 표시/항목 의미 매뉴얼 생성 대상 여부."""
    if op.failure_modes or not op.table_en:
        return False
    surface = " ".join([op.action or "", op.api_path or ""])
    return bool(_DISPLAY_ACTION_RE.search(surface))


def manual_candidates(ops: list[ExtractedOperation], include_display: bool = False) -> list[ExtractedOperation]:
    if not include_display:
        return [op for op in ops if is_manual_candidate(op)]
    return [op for op in ops if is_manual_candidate(op) or is_display_candidate(op)]


def _manual_type_for(op: ExtractedOperation) -> str:
    return "failure" if is_manual_candidate(op) else "display"


def _display_comment_for_branch(comment: str, codes: dict[str, str]) -> str:
    text = re.sub(r"\([^)]*(?:[A-Z0-9_]+:)[^)]*\)", "", comment or "").strip()
    if codes:
        meanings = ", ".join(dict.fromkeys(v.strip() for v in codes.values() if v.strip()))
        if meanings:
            text = f"{text}: {meanings}" if text else meanings
    return text or comment


def _columns_for_display(op: ExtractedOperation, table: str, columns: dict[str, str]) -> list[str]:
    selected = op.display_columns.get(table) or []
    if selected:
        return [c for c in selected if c in columns]
    return list(columns)


def _static_display_branch(op: ExtractedOperation) -> str:
    table_names = ", ".join(op.table_ko or op.table_en)
    lines = [
        f"# {op.screen_ko} — 화면 표시 항목",
        "",
        f"{op.screen_ko} 화면은 {table_names} 정보를 기준으로 표시됩니다.",
        "",
        "## 주요 표시 항목",
    ]
    added = 0
    for table, n in op.notation.items():
        columns = n.get("columns", {})
        codes_by_col = n.get("code_values", {})
        for col in _columns_for_display(op, table, columns):
            meaning = _display_comment_for_branch(columns.get(col, ""), codes_by_col.get(col, {}))
            if not meaning:
                continue
            lines.append(f"- {meaning}")
            added += 1
    if not added:
        lines.append(f"- {table_names}")
    lines += [
        "",
        "## 안내 범위",
        "이 매뉴얼은 화면에 표시되는 항목의 의미를 설명합니다. 조회 실패 원인은 코드에서 확인된 실패 조건이 있을 때만 별도 매뉴얼에서 안내합니다.",
    ]
    return "\n".join(lines)


def _static_display_it(op: ExtractedOperation) -> str:
    lines = [
        f"# {op.screen_ko} / {op.action} 표시 항목 (IT)",
        "",
        "## 조회 흐름",
        " → ".join(op.lineage),
        "",
        "## 표시 컬럼",
    ]
    for table, n in op.notation.items():
        columns = n.get("columns", {})
        codes_by_col = n.get("code_values", {})
        selected = _columns_for_display(op, table, columns)
        if not selected:
            continue
        lines.append(f"### {table}")
        for col in selected:
            comment = columns.get(col, "")
            suffix = ""
            if codes_by_col.get(col):
                suffix = " (" + ", ".join(f"{k}={v}" for k, v in codes_by_col[col].items()) + ")"
            lines.append(f"- {col}: {comment}{suffix}")
    lines += [
        "",
        "## 안내 범위",
        "실패 조건이 추출되지 않은 조회/표시 매뉴얼이다. 조회 실패 원인은 이 매뉴얼에서 단정하지 않는다.",
    ]
    return "\n".join(lines)


def build_manual_id(op: ExtractedOperation, manual_type: str) -> str:
    suffix = op.action
    if manual_type == "display":
        suffix = f"{suffix}_display"
    return f"manual_{op.screen_id.lower()}_{suffix}"


def display_manual_candidates(ops: list[ExtractedOperation]) -> list[ExtractedOperation]:
    return [op for op in ops if is_display_candidate(op)]


def failure_manual_candidates(ops: list[ExtractedOperation]) -> list[ExtractedOperation]:
    return [op for op in ops if is_manual_candidate(op)]


def _code_annot(condition: str, notation: dict) -> str:
    annots: list[str] = []
    for n in notation.values():
        for codes in n["code_values"].values():
            for code, ko in codes.items():
                if f'"{code}"' in condition or f"'{code}'" in condition:
                    annots.append(f"{code}={ko}")
    return ", ".join(dict.fromkeys(annots))


def _static_branch(op: ExtractedOperation) -> str:
    lines = [
        f"# {op.screen_ko} — 처리가 안 될 때",
        "",
        f"{op.screen_ko} 화면에서 처리가 안 되는 경우 아래를 확인해 주세요.",
        "",
        "## 가능한 원인과 확인 사항",
    ]
    for i, fm in enumerate(op.failure_modes, 1):
        cause = fm.cause.rstrip(".")
        hint = _strip_internal(fm.meaning)
        lines.append(f"{i}. {cause}" + (f" — {hint}." if hint else "."))
    lines += [
        "",
        "## 그래도 안 되면",
        f"위 사항을 확인한 뒤에도 같은 오류가 계속되면, 화면명({op.screen_ko})·수행 작업·오류 문구를 정리해 IT 담당자에게 전달해 주세요.",
    ]
    return "\n".join(lines)


def _static_it(op: ExtractedOperation) -> str:
    lines = [f"# {op.screen_ko} / {op.action} (IT)", "", "## 처리 흐름", " → ".join(op.lineage), "", "## 실패 조건"]
    for fm in op.failure_modes:
        ann = _code_annot(fm.condition, op.notation)
        lines.append(f"- [{fm.error_code}] {fm.cause}")
        lines.append(f"  - 조건: `{fm.condition}`" + (f"  ({ann})" if ann else ""))
        if fm.meaning:
            lines.append(f"  - 의미: {fm.meaning}")
        ev = ", ".join(f"{p.path.split('/')[-1]}:{p.lines}" for p in fm.evidence if p.lines)
        if ev:
            lines.append(f"  - 근거: {ev}")
    if op.notation:
        lines += ["", "## 표기의미"]
        for tbl, n in op.notation.items():
            for col, codes in n["code_values"].items():
                lines.append(f"- {tbl}.{col}: " + ", ".join(f"{k}={v}" for k, v in codes.items()))
    return "\n".join(lines)


class ManualBuilder:
    def __init__(self, generator: Generator | None = None):
        self.generator = generator or Generator(
            settings.llm_base_url, settings.llm_api_key, settings.llm_model, settings.llm_timeout_s
        )

    def _polish(self, system: str, draft: str) -> str | None:
        try:
            out = self.generator.rephrase(system, draft)
            return out.strip() if out and out.strip() else None
        except GeneratorError:
            return None

    def build(self, op: ExtractedOperation, use_llm: bool = True, manual_type: str | None = None) -> Manual:
        manual_type = manual_type or _manual_type_for(op)
        if manual_type == "display":
            branch = _static_display_branch(op)
            it = _static_display_it(op)
        else:
            branch = _static_branch(op)
            it = _static_it(op)
        if use_llm and manual_type == "failure":
            polished_b = self._polish(BRANCH_SYS, branch)
            if polished_b and is_branch_clean(polished_b):  # LLM 출력이 새지 않을 때만 채택
                branch = polished_b
            polished_it = self._polish(IT_SYS, it)
            if polished_it:
                it = polished_it
        return Manual(
            id=build_manual_id(op, manual_type),
            screen_id=op.screen_id,
            screen_ko=op.screen_ko,
            action=op.action,
            manual_type=manual_type,
            api_path=op.api_path,
            table_en=op.table_en,
            table_ko=op.table_ko,
            branch_md=branch,
            it_md=it,
            facts={
                "failure_modes": [asdict(fm) for fm in op.failure_modes],
                "notation": op.notation,
                "display_columns": op.display_columns,
            },
            lineage_ref=op.lineage,
            provenance=op.provenance,
            status="draft",
            version=1,
        )
