"""Java/Spring 파서 — 컨트롤러 매핑 + 서비스 실패모드/호출/주석.

regex 기반(프로토타입 한계, 향후 AST). 추출:
- Controller: @RequestMapping 접두 + @PostMapping 등 → api_path, 메서드, 호출하는 Service.
- Service: 메서드별 throw(코드·메시지) + 직전 한글 주석 + if 조건(verbatim) + Mapper 호출.
"""
from __future__ import annotations

import re
from pathlib import Path

_METHOD_RE = re.compile(
    r"(?:public|private|protected)\s+[\w<>\[\],\s]+?\s+(\w+)\s*\(([^)]*)\)\s*(?:throws[^{]+)?\{"
)
_MAPPING_RE = re.compile(r'@(Get|Post|Put|Patch|Delete)Mapping\(\s*"([^"]*)"')
_REQ_MAP_RE = re.compile(r'@RequestMapping\(\s*"([^"]+)"')
_FIELD_RE = re.compile(r"\b(?:private|protected|public)\s+(?:final\s+)?([A-Z]\w+)\s+(\w+)\s*;")
_CALL_RE = re.compile(r"(\w+)\.(\w+)\s*\(")
_THROW_RE = re.compile(r'throw\s+new\s+\w+\(\s*"([^"]*)"\s*,\s*"([^"]*)"\s*\)')
_IF_RE = re.compile(r"\bif\s*\((.*)\)\s*\{?\s*$")


def _join_path(prefix: str, path: str) -> str:
    left = (prefix or "").rstrip("/")
    right = (path or "").lstrip("/")
    joined = f"{left}/{right}" if right else left
    return joined if joined.startswith("/") else "/" + joined


def _find_matching_brace(text: str, open_idx: int) -> int:
    depth = 0
    quote: str | None = None
    esc = False
    for i in range(open_idx, len(text)):
        c = text[i]
        if quote:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == quote:
                quote = None
        elif c in "\"'":
            quote = c
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i
    return len(text) - 1


def _head_before(text: str, start: int) -> list[str]:
    """메서드 직전의 연속된 @어노테이션 / // 주석 줄."""
    lines = text[:start].split("\n")
    out: list[str] = []
    i = len(lines) - 2  # 메서드가 시작되는 줄의 앞 조각은 건너뜀
    while i >= 0:
        s = lines[i].strip()
        if s.startswith("@") or s.startswith("//"):
            out.insert(0, s)
            i -= 1
        else:
            break
    return out


def _failure_modes(body: str) -> list[dict]:
    """본문을 줄 단위로 훑어 직전 주석·조건을 throw에 묶는다."""
    fms: list[dict] = []
    last_comment = ""
    last_condition = ""
    for raw in body.split("\n"):
        line = raw.strip()
        if line.startswith("//"):
            last_comment = line[2:].strip()
            continue
        ifm = _IF_RE.search(line)
        if ifm:
            last_condition = ifm.group(1).strip()
        thr = _THROW_RE.search(line)
        if thr:
            fms.append(
                {
                    "error_code": thr.group(1),
                    "message": thr.group(2),
                    "condition": last_condition,
                    "comment": last_comment,
                }
            )
            last_comment = ""
            last_condition = ""
    return fms


def parse_java(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    cm = re.search(r"\bclass\s+(\w+)", text)
    cls = cm.group(1) if cm else path.stem
    is_ctrl = "@RestController" in text or "@Controller" in text
    is_svc = "@Service" in text or cls.endswith("Service")
    kind = "controller" if is_ctrl else ("service" if is_svc else "other")
    rm = _REQ_MAP_RE.search(text)
    prefix = rm.group(1) if rm else ""
    fields = {var: typ for typ, var in _FIELD_RE.findall(text)}

    methods: dict[str, dict] = {}
    for m in _METHOD_RE.finditer(text):
        name = m.group(1)
        if name == cls:  # 생성자 방어
            continue
        close = _find_matching_brace(text, m.end() - 1)
        body = text[m.end() : close]
        head = _head_before(text, m.start())
        comment = " ".join(h[2:].strip() for h in head if h.startswith("//")).strip()
        api_path = http = None
        for h in head:
            mm = _MAPPING_RE.search(h)
            if mm:
                http = mm.group(1).upper()
                api_path = _join_path(prefix, mm.group(2))
                break
        resolved: list[str] = []
        for owner, meth in _CALL_RE.findall(body):
            if owner in fields:
                key = f"{fields[owner]}.{meth}"
                if key not in resolved:
                    resolved.append(key)
        methods[name] = {
            "api_path": api_path,
            "http_method": http,
            "comment": comment,
            "calls": resolved,
            "failure_modes": _failure_modes(body),
            "lines": f"{text[: m.start()].count(chr(10)) + 1}-{text[:close].count(chr(10)) + 1}",
        }
    return {"class": cls, "kind": kind, "prefix": prefix, "fields": fields, "methods": methods, "path": str(path)}
