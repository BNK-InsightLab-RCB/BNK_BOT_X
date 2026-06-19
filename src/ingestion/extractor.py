"""P1 — Extractor (소스 → 구조화된 사실).

스캔 → 파서 4종 → 오퍼레이션(화면 × 액션 = 하나의 lineage 체인)으로 링크.
출력 = ExtractedOperation 리스트. 측정① = 슬라이스 화면의 체인을 정확히 뽑는가.
"""
from __future__ import annotations

from pathlib import Path

from src.ingestion.parsers.ddl import parse_ddl
from src.ingestion.parsers.frontend import build_frontend_index, parse_frontend
from src.ingestion.parsers.java import parse_java
from src.ingestion.parsers.mybatis import parse_mybatis
from src.models import ExtractedOperation, FailureMode, Provenance

_FRONTEND_EXT = {".vue", ".js", ".ts", ".jsx", ".tsx", ".html"}


def _uniq(items) -> list:
    out, seen = [], set()
    for x in items:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


class Extractor:
    def extract(self, source_dir: Path) -> list[ExtractedOperation]:
        source_dir = Path(source_dir)
        ddl: dict[str, dict] = {}
        mybatis: dict[str, dict] = {}
        controllers: dict[str, dict] = {}
        services: dict[str, dict] = {}
        frontends: list[dict] = []
        frontend_index = build_frontend_index(source_dir)

        for p in sorted(source_dir.rglob("*")):
            if not p.is_file():
                continue
            suffix = p.suffix.lower()
            if suffix == ".sql":
                for table in parse_ddl(p):
                    ddl[table["table_en"]] = table
            elif suffix == ".xml":
                mybatis.update(parse_mybatis(p))
            elif suffix == ".java":
                self._index_java(parse_java(p), controllers, services)
            elif suffix in _FRONTEND_EXT:
                fe = parse_frontend(p, frontend_index)
                if fe["screen_id"] or fe["api_calls"]:
                    frontends.append(fe)

        return self._link(ddl, mybatis, controllers, services, frontends)

    def _index_java(self, pj: dict, controllers: dict, services: dict) -> None:
        cls = pj["class"]
        for name, md in pj["methods"].items():
            if pj["kind"] == "controller" and md["api_path"]:
                service_call = next(
                    (c for c in md["calls"] if c.split(".")[0].endswith("Service")), None
                )
                controllers[md["api_path"]] = {
                    "service_call": service_call,
                    "comment": md["comment"],
                    "path": pj["path"],
                }
            elif pj["kind"] == "service":
                mapper_calls = [c for c in md["calls"] if c.split(".")[0].endswith("Mapper")]
                services[f"{cls}.{name}"] = {
                    "failure_modes": md["failure_modes"],
                    "mapper_calls": mapper_calls,
                    "comment": md["comment"],
                    "path": pj["path"],
                    "lines": md["lines"],
                }

    def _link(self, ddl, mybatis, controllers, services, frontends) -> list[ExtractedOperation]:
        ops: list[ExtractedOperation] = []
        for fe in frontends:
            for call in fe["api_calls"]:
                api_path = call["api_path"]
                action = api_path.rstrip("/").split("/")[-1]
                ctrl = controllers.get(api_path)
                service_call = ctrl["service_call"] if ctrl else None
                svc = services.get(service_call) if service_call else None
                mapper_calls = svc["mapper_calls"] if svc else []

                tables: list[str] = []
                for mc in mapper_calls:
                    mb = mybatis.get(mc)
                    if mb:
                        tables += mb["tables"]
                tables = _uniq(tables)
                table_ko = _uniq(ddl[t]["table_ko"] for t in tables if ddl.get(t, {}).get("table_ko"))
                notation = {
                    t: {"columns": ddl[t]["columns"], "code_values": ddl[t]["code_values"]}
                    for t in tables
                    if t in ddl
                }

                lineage = _uniq(
                    [fe["screen_id"], api_path]
                    + ([service_call] if service_call else [])
                    + mapper_calls
                    + tables
                )

                fms = [
                    FailureMode(
                        cause=f["message"],
                        error_code=f["error_code"],
                        condition=f["condition"],
                        meaning=f["comment"],
                        evidence=[Provenance(path=svc["path"], lines=svc["lines"])],
                    )
                    for f in (svc["failure_modes"] if svc else [])
                ]

                comments = _uniq(
                    [ctrl["comment"] if ctrl else "", svc["comment"] if svc else ""]
                    + [f["comment"] for f in (svc["failure_modes"] if svc else [])]
                    + [mybatis[mc]["comment"] for mc in mapper_calls if mc in mybatis]
                )

                prov_paths = _uniq(
                    [fe["path"]]
                    + ([ctrl["path"]] if ctrl else [])
                    + ([svc["path"]] if svc else [])
                    + [mybatis[mc]["path"] for mc in mapper_calls if mc in mybatis]
                    + [ddl[t]["path"] for t in tables if t in ddl]
                )

                ops.append(
                    ExtractedOperation(
                        screen_id=fe["screen_id"],
                        screen_ko=fe["screen_ko"],
                        action=action,
                        api_path=api_path,
                        lineage=lineage,
                        table_en=tables,
                        table_ko=table_ko,
                        failure_modes=fms,
                        comments=comments,
                        notation=notation,
                        provenance=[Provenance(path=x) for x in prov_paths],
                    )
                )
        return ops
