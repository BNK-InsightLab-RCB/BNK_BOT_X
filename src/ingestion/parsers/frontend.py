"""프론트 파서 — 화면 식별/이름 + API 호출.

화면(screen_id, screen_ko)을 api_path에 연결해 오퍼레이션의 시작점을 만든다.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_SCREEN_RE = re.compile(r"""screenId\s*:\s*["']([^"']+)["']""")
_HEADING_RE = re.compile(r"<h[12][^>]*>(.*?)</h[12]>", re.DOTALL | re.IGNORECASE)
_AXIOS_RE = re.compile(
    r"""axios\.(get|post|put|patch|delete)\s*\(\s*["']([^"']+)["']""", re.IGNORECASE
)
_API_FN_RE = re.compile(
    r"""export\s+const\s+(\w+)\s*=\s*(?:\([^)]*\)|\w+)?\s*=>\s*api\.(get|post|put|patch|delete)\s*\(\s*([`'"])(.*?)\3""",
    re.DOTALL | re.IGNORECASE,
)
_BASE_URL_RE = re.compile(r"""baseURL\s*:\s*["'][^"']*?/api["']""")
_IMPORT_ALIAS_RE = re.compile(r"""import\s+\*\s+as\s+(\w+)\s+from\s+["']([^"']+)["']""")
_EXPORT_DEFAULT_FN_RE = re.compile(r"\bexport\s+default\s+function\s+(\w+)")
_ROUTE_RE = re.compile(r"""<Route\s+path=["']([^"']+)["']\s+element=\{<(\w+)\s*/>\}""")
_IMPORT_PAGE_RE = re.compile(r"""import\s+(\w+)\s+from\s+["']\./pages/([^"']+)["']""")
_MENU_ITEM_RE = re.compile(
    r"""\{\s*key:\s*["'][^"']+["']\s*,\s*label:\s*["']([^"']+)["']\s*,\s*path:\s*["']([^"']+)["']""",
    re.DOTALL,
)


def _normalize_api_path(path: str, has_api_base: bool = False) -> str:
    p = re.sub(r"\$\{([^}]+)\}", r"{\1}", (path or "").strip())
    if not p.startswith("/"):
        p = "/" + p
    if has_api_base and not p.startswith("/api/") and p != "/api":
        p = "/api" + p
    return p


def _screen_id_from_route(route_path: str, fallback: str) -> str:
    if route_path:
        return re.sub(r"[^0-9A-Za-z]+", "_", route_path.strip("/")).strip("_").upper()
    return re.sub(r"(?<!^)(?=[A-Z])", "_", fallback.replace("Page", "")).upper()


def _clean_text(raw: str) -> str:
    text = re.sub(r"<[^>]+>", "", raw or "")
    text = re.sub(r"[^\w가-힣\s()%./-]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _service_module_name(import_path: str) -> str:
    return Path(import_path).stem


def build_frontend_index(source_dir: Path) -> dict[str, Any]:
    """React service-layer 패턴용 인덱스.

    00.BNK_Hackathon은 Page → services/*Api.js → axios instance(baseURL=/api) 구조다.
    화면명은 MENU_ITEMS, route는 App.jsx에 있다. 기존 Vue 샘플은 이 인덱스 없이도 동작한다.
    """
    source_dir = Path(source_dir)
    services: dict[str, dict[str, dict[str, str]]] = {}
    api_base_file = next(source_dir.rglob("api.js"), None)
    has_api_base = False
    if api_base_file:
        has_api_base = bool(_BASE_URL_RE.search(api_base_file.read_text(encoding="utf-8")))
    for p in source_dir.rglob("*Api.js"):
        text = p.read_text(encoding="utf-8")
        module = p.stem
        services[module] = {}
        for fn, method, _, api_path in _API_FN_RE.findall(text):
            services[module][fn] = {
                "http_method": method.upper(),
                "api_path": _normalize_api_path(api_path, has_api_base),
            }

    component_routes: dict[str, str] = {}
    app = next(source_dir.rglob("App.jsx"), None)
    if app:
        text = app.read_text(encoding="utf-8")
        imported = {name: stem for name, stem in _IMPORT_PAGE_RE.findall(text)}
        for route_path, component in _ROUTE_RE.findall(text):
            if component in imported:
                component_routes[component] = route_path

    menu_labels: dict[str, str] = {}
    constants = next(source_dir.rglob("constants.js"), None)
    if constants:
        text = constants.read_text(encoding="utf-8")
        menu_labels = {path: label for label, path in _MENU_ITEM_RE.findall(text)}

    return {"services": services, "component_routes": component_routes, "menu_labels": menu_labels}


def parse_frontend(path: Path, index: dict[str, Any] | None = None) -> dict:
    text = path.read_text(encoding="utf-8")
    sid = _SCREEN_RE.search(text)
    heading = _HEADING_RE.search(text)
    screen_ko = _clean_text(heading.group(1)) if heading else ""
    calls: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for m in _AXIOS_RE.finditer(text):
        key = (m.group(1).upper(), m.group(2))
        if key not in seen:
            seen.add(key)
            calls.append({"http_method": m.group(1).upper(), "api_path": _normalize_api_path(m.group(2))})

    index = index or {}
    component_match = _EXPORT_DEFAULT_FN_RE.search(text)
    component = component_match.group(1) if component_match else path.stem
    route_path = index.get("component_routes", {}).get(component, "")
    if route_path:
        screen_ko = index.get("menu_labels", {}).get(route_path, screen_ko)
    aliases = {_service_module_name(import_path): alias for alias, import_path in _IMPORT_ALIAS_RE.findall(text)}
    alias_to_module = {alias: module for module, alias in aliases.items()}
    services = index.get("services", {})
    for alias, fn in re.findall(r"\b(\w+)\.(\w+)\s*\(", text):
        # import * as alias 면 그 모듈, 아니면 호출 객체명이 서비스 모듈명과 같으면 직접 매칭.
        # (실코드엔 import 누락/스타일 편차가 있어 객체명 직접 매칭이 더 robust)
        module = alias_to_module.get(alias) or (alias if alias in services else None)
        call = services.get(module, {}).get(fn) if module else None
        if not call:
            continue
        key = (call["http_method"], call["api_path"])
        if key not in seen:
            seen.add(key)
            calls.append({**call, "fn": fn})  # fn = 의미있는 액션명(executeLoan 등)

    return {
        "screen_id": sid.group(1) if sid else (_screen_id_from_route(route_path, component) if route_path or calls else ""),
        "screen_ko": screen_ko,
        "api_calls": calls,
        "path": str(path),
    }
