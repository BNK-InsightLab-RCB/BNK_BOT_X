"""데이터 계약 — 모든 단계가 바라보는 척추.

- ExtractedOperation : P1 Extractor 출력(소스에서 뽑은 구조화된 사실).
- Manual             : P2 출력 = 검수·동결되는 지식 단위.
                       JSON 레코드 + 본문(branch_md / it_md)만 Markdown.

매뉴얼 1개 == 오퍼레이션 1개 == 화면 × 액션 == 하나의 lineage 체인.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Provenance:
    """근거 위치 — 매뉴얼의 모든 사실은 소스 위치로 추적된다."""

    path: str
    lines: str = ""
    commit: str | None = None


@dataclass
class FailureMode:
    """오퍼레이션이 실패할 수 있는 한 가지 방식(매뉴얼 안의 한 항목)."""

    cause: str  # 오류 메시지/짧은 라벨: "경비 저장 권한이 없습니다."
    error_code: str = ""  # 코드값: "E_AUTH"
    condition: str = ""  # 코드 근거 조건(verbatim): "!hasAuthority('EXPENSE_SAVE')"
    meaning: str = ""  # 업무 의미(한글 주석): "저장 권한이 없으면 처리 불가"
    action: str = ""  # 담당자 조치(P2에서 생성): "권한 담당자에게 EXPENSE_SAVE 신청"
    evidence: list[Provenance] = field(default_factory=list)


@dataclass
class ExtractedOperation:
    """P1 Extractor 출력 — 오퍼레이션 1개(하나의 lineage 체인)에 대한 사실."""

    screen_id: str
    screen_ko: str = ""
    action: str = ""
    api_path: str | None = None
    lineage: list[str] = field(default_factory=list)  # 화면→API→Service→Mapper→테이블
    table_en: list[str] = field(default_factory=list)
    table_ko: list[str] = field(default_factory=list)
    failure_modes: list[FailureMode] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)  # 코드 위치에 묶인 한글 주석
    notation: dict[str, Any] = field(default_factory=dict)  # 표기의미: {table: {columns, code_values}}
    provenance: list[Provenance] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Manual:
    """P2 출력 — 검수·동결되는 지식 단위(데이터 계약)."""

    id: str
    screen_id: str
    screen_ko: str = ""
    action: str = ""
    api_path: str | None = None
    table_en: list[str] = field(default_factory=list)
    table_ko: list[str] = field(default_factory=list)
    branch_md: str = ""  # 영업점 담당자용 Markdown 산문
    it_md: str = ""  # IT 담당자용 Markdown 산문
    facts: dict[str, Any] = field(default_factory=dict)
    lineage_ref: list[str] = field(default_factory=list)
    provenance: list[Provenance] = field(default_factory=list)
    status: str = "draft"  # draft | frozen
    version: int = 1
    reviewed_at: str = ""  # 검수·동결 시각(감사)
    reviewed_by: str = ""  # 검수자(감사)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Manual":
        known = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        known["provenance"] = [Provenance(**p) for p in d.get("provenance", [])]
        return cls(**known)

    def body_for(self, role: str) -> str:
        return self.branch_md if role == "branch" else self.it_md

    def payload(self, role: str) -> dict[str, Any]:
        """Qdrant payload(역할별). 본문은 역할에 맞는 것만 임베딩·저장."""
        return {
            "manual_id": self.id,
            "role": role,
            "screen_id": self.screen_id,
            "screen_ko": self.screen_ko,
            "action": self.action,
            "api_path": self.api_path,
            "table_en": self.table_en,
            "table_ko": self.table_ko,
            "body": self.body_for(role),
            "status": self.status,
            "version": self.version,
        }
