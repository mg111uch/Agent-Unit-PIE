"""tool_anatomy: deterministic registry introspection.

Two modes:
  tool_anatomy(name="Read")          -> deep trace: category, registration line,
      implementation line, mcp_expose, enabled_now, schema params, every cross-file
      reference (prompt fragments, mock scenarios, tests, stepper._EDIT_TOOLS,
      audit._WRITE_TOOLS, session_state observers, mcp_server), merge/rename history.
  tool_anatomy()                          -> inventory of all tools grouped by category
      with impl + registration locations, resolved config, and a stale-reference scan
      (names referenced in docs/mocks but not registered).

Registered under CAT_META (always MCP-exposed).
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from agent_core.tools.registry import (
    CAT_FILE, CAT_KERNEL, CAT_SIM, CAT_META, CAT_SEARCH, CAT_GIT, CAT_CODE_RAG, CAT_OBSERVER, CAT_DEBATE,
)
from agent_core.config import (
    CODEBASE_ROOT,
    resolve_active_tool_packs,
    resolve_active_tool_mode,
    resolve_active_tool_names,
    resolve_mcp_always_expose,
)

_CATEGORY_LABELS = {
    CAT_FILE: "CAT_FILE", CAT_KERNEL: "CAT_KERNEL", CAT_SIM: "CAT_SIM",
    CAT_META: "CAT_META", CAT_SEARCH: "CAT_SEARCH", CAT_GIT: "CAT_GIT",
    CAT_CODE_RAG: "CAT_CODE_RAG", CAT_OBSERVER: "CAT_OBSERVER", CAT_DEBATE: "CAT_DEBATE",
}

_MCP_ALWAYS = {CAT_SEARCH} | ({CAT_META} if resolve_mcp_always_expose() == "meta" else set())
_MCP_NEVER = {CAT_FILE}
_CAT_ORDER = [CAT_FILE, CAT_META, CAT_SEARCH, CAT_KERNEL, CAT_GIT, CAT_CODE_RAG, CAT_OBSERVER, CAT_SIM, CAT_DEBATE]

_GROUP_CAPS = {
    "prompt_fragments": 8, "mock_scenarios": 4, "tests": 4, "stepper": 4,
    "audit": 4, "session_state": 4, "mcp_server": 4, "core": 8,
}

_HISTORY_KW = ("duplicate", "merged", "renamed", "replaced", "supersed", "deprecat", "converted")
_NEG_HISTORY = ("not a duplicate", "not duplicate", "no duplicate", "not renamed")

_reg_cache: dict = {"mtime": -1, "lines": {}}
_path_cache: dict = {}


def _word_pattern(name: str):
    return re.compile(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", re.IGNORECASE)


def _cached_paths(key: str, builder):
    if key not in _path_cache:
        _path_cache[key] = builder()
    return _path_cache[key]


def _registration_lines() -> dict:
    init = Path(CODEBASE_ROOT) / "agent_core" / "tools" / "__init__.py"
    try:
        mtime = init.stat().st_mtime
    except OSError:
        return {}
    if _reg_cache["mtime"] == mtime and _reg_cache["lines"]:
        return _reg_cache["lines"]
    lines = {}
    try:
        src = init.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        _reg_cache.update(mtime=mtime, lines=lines)
        return lines
    for i, line in enumerate(src, 1):
        m = re.match(r'\s*\(\s*"([A-Za-z_][A-Za-z0-9_]*)",', line)
        if m:
            lines.setdefault(m.group(1), i)
    _reg_cache.update(mtime=mtime, lines=lines)
    return lines


def _core_py_paths() -> list:
    core = Path(CODEBASE_ROOT) / "agent_core"
    covered = {
        core / "providers" / "mock_provider.py",
        core / "loop" / "stepper.py",
        core / "loop" / "_helpers.py",
        core / "server" / "audit.py",
        core / "loop" / "session_state.py",
        core / "mcp_server.py",
        core / "tools" / "tool_introspect.py",
        core / "tools" / "__init__.py",
    }
    out = []
    for f in sorted(core.rglob("*.py")):
        if f in covered or f.name == "__init__.py":
            continue
        out.append(f)
    return out


def _tests_paths() -> list:
    root = Path(CODEBASE_ROOT)
    return sorted(p for p in root.rglob("*test*.py") if not any(seg.startswith(".") for seg in p.parts))


def _match_files(paths, name, cap: int, skip_impl=None) -> list:
    pat = _word_pattern(name)
    hits = []
    for p in paths:
        if not p or not p.exists():
            continue
        if skip_impl is not None and os.path.abspath(str(p)) == skip_impl:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pat.search(line):
                hits.append((os.path.relpath(p, CODEBASE_ROOT), i, line.strip()[:90]))
                if len(hits) >= cap:
                    return hits
    return hits


def _scan_references(name: str) -> dict:
    from agent_core.tools import _IMPL_INDEX
    impl = _IMPL_INDEX.get(name)
    impl_abs = os.path.abspath(impl[0]) if impl else None
    core = Path(CODEBASE_ROOT)
    groups = {
        "prompt_fragments": _cached_paths("pf", lambda: sorted((core / "prompt_fragments").glob("*.md"))),
        "mock_scenarios": [core / "agent_core" / "providers" / "mock_provider.py"],
        "tests": _cached_paths("tests", _tests_paths),
        "stepper": [core / "agent_core" / "loop" / "stepper.py", core / "agent_core" / "loop" / "_helpers.py"],
        "audit": [core / "agent_core" / "server" / "audit.py"],
        "session_state": [core / "agent_core" / "loop" / "session_state.py"],
        "mcp_server": [core / "agent_core" / "mcp_server.py"],
        "core": _cached_paths("core", _core_py_paths),
    }
    out = {}
    for label, paths in groups.items():
        hits = _match_files(paths, name, _GROUP_CAPS[label], skip_impl=impl_abs)
        if hits:
            out[label] = hits
    return out


def _schema_params(name: str):
    from agent_core.tools import registry
    for s in registry.schemas_list:
        if s.get("name") == name:
            params = (s.get("parameters") or {}).get("properties") or {}
            required = (s.get("parameters") or {}).get("required") or []
            return params, required
    return {}, []


def _render_params(properties, required) -> list:
    out = []
    for pname, spec in properties.items():
        ptype = spec.get("type", "?")
        req = "required" if pname in required else "optional"
        desc = str(spec.get("description", ""))[:70]
        out.append(f"    {pname} ({ptype}, {req})" + (f" — {desc}" if desc else ""))
    return out


def _mcp_expose(category: str) -> str:
    active = set(resolve_active_tool_packs())
    if category in _MCP_ALWAYS:
        return f"yes (always-on: {', '.join(sorted(_MCP_ALWAYS))})"
    if category in _MCP_NEVER:
        return "no (CAT_FILE never exposed)"
    if category in active:
        return "yes (pack active)"
    return f"no (pack '{category}' off in tool_packs)"


def _enabled_now(name: str) -> str:
    mode = resolve_active_tool_mode()
    if mode == "all":
        return "yes (tool_mode=all)"
    return "yes" if name in resolve_active_tool_names() else f"no (tool_mode={mode} excludes it)"


def _is_exposed(category: str) -> bool:
    if category in _MCP_ALWAYS:
        return True
    if category in _MCP_NEVER:
        return False
    return category in set(resolve_active_tool_packs())


def _is_enabled(name: str) -> bool:
    mode = resolve_active_tool_mode()
    if mode == "all":
        return True
    return name in resolve_active_tool_names()


def _history(name: str) -> list:
    sess = Path(CODEBASE_ROOT).parent / "sessions_analysis"
    out = []
    if not sess.is_dir():
        return out
    pat = re.compile(r"`" + re.escape(name) + r"`", re.IGNORECASE)
    for f in sorted(sess.glob("*.md")):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line in text.splitlines():
            low = line.lower()
            if not pat.search(line) or any(k in low for k in _NEG_HISTORY):
                continue
            if any(k in low for k in _HISTORY_KW):
                snip = line.strip().strip("#*|` ").strip()
                if snip:
                    out.append(f"{f.stem}: {snip[:130]}")
                if len(out) >= 5:
                    return out
    return out


def _stale_hint(name: str) -> str:
    core = Path(CODEBASE_ROOT)
    candidates = list((core / "prompt_fragments").glob("*.md"))
    candidates.append(core / "agent_core" / "providers" / "mock_provider.py")
    sess = Path(CODEBASE_ROOT).parent / "sessions_analysis"
    if sess.is_dir():
        candidates += list(sess.glob("*.md"))
    pat = _word_pattern(name)
    hits = []
    for f in candidates:
        if not f.exists():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pat.search(line):
                hits.append(f"{os.path.relpath(f, CODEBASE_ROOT)}:{i}")
                break
        if len(hits) >= 6:
            break
    if hits:
        return f"Not registered but still referenced by: {', '.join(hits)} (likely renamed/removed)."
    return "No references found in docs/mocks/sessions."


def _config_header() -> str:
    from agent_core.tools import registry
    packs = resolve_active_tool_packs()
    mode = resolve_active_tool_mode()
    return (
        f"active packs: {', '.join(packs) if packs else '(none)'} | tool_mode: {mode} | "
        f"tools: {registry.tool_count} | mcp policy: always={','.join(sorted(_MCP_ALWAYS))}, CAT_FILE never, others if pack on"
    )


def _deep_trace(name: str) -> str:
    from agent_core.tools import registry, _IMPL_INDEX
    if not registry.has_tool(name):
        return f"'{name}' is not a registered tool.\n  {_stale_hint(name)}"
    cat = registry.get_category(name)
    reg_lines = _registration_lines()
    impl = _IMPL_INDEX.get(name)
    params, required = _schema_params(name)
    impl_txt = os.path.relpath(impl[0], CODEBASE_ROOT) if impl else "(unknown)"
    lines = [
        name,
        f"  category:       {_CATEGORY_LABELS.get(cat, cat)}",
        f"  registration:   {f'__init__.py:{reg_lines.get(name)}' if reg_lines.get(name) else '__init__.py:?'}",
        f"  implementation: {impl_txt + ':' + str(impl[1]) if impl else '(unknown)'}",
        f"  mcp_expose:     {_mcp_expose(cat)}",
        f"  enabled_now:    {_enabled_now(name)}",
    ]
    hist = _history(name)
    lines.append("  history:        " + ("; ".join(hist) if hist else "(none)"))
    if params:
        lines.append("  schema params:")
        lines.extend(_render_params(params, required))
    refs = _scan_references(name)
    if refs:
        for label in ("prompt_fragments", "mock_scenarios", "tests", "stepper",
                      "audit", "session_state", "mcp_server", "core"):
            matches = refs.get(label)
            if not matches:
                continue
            lines.append(f"  references [{label}]:")
            for rel, ln, snip in matches:
                lines.append(f"    {rel}:{ln}  {snip}")
    else:
        lines.append("  references: (none beyond registration)")
    return "\n".join(lines)


def _collect_stale_refs() -> dict:
    from agent_core.tools import registry
    registered = set(registry.tool_names)
    core = Path(CODEBASE_ROOT)
    candidates = [core / "agent_core" / "providers" / "mock_provider.py"]
    candidates += list((core / "prompt_fragments").glob("*.md"))
    sess = Path(CODEBASE_ROOT).parent / "sessions_analysis"
    if sess.is_dir():
        candidates += list(sess.glob("*.md"))
    name_pat = re.compile(r'"name":\s*"([a-z_][a-z0-9_]*)')
    call_pat = re.compile(r"(?<![A-Za-z0-9_])([a-z_][a-z0-9_]*)\s*\(")
    found: dict = {}
    for f in candidates:
        if not f.exists():
            continue
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if f.name == "mock_provider.py":
            tokens = set(name_pat.findall(text))
        else:
            tokens = {t for t in call_pat.findall(text) if "_" in t}
        for tok in tokens:
            if len(tok) < 3 or tok.startswith("_") or tok in registered:
                continue
            found.setdefault(tok, set()).add(os.path.relpath(f, CODEBASE_ROOT))
    return found


def _inventory(category=None) -> str:
    from agent_core.tools import registry, _IMPL_INDEX
    lines = [_config_header()]
    reg_lines = _registration_lines()
    grouped = {}
    for n in registry.tool_names:
        cat = registry.get_category(n)
        if category and cat != category:
            continue
        grouped.setdefault(cat, []).append(n)
    ordered = [c for c in _CAT_ORDER if c in grouped] + [c for c in grouped if c not in _CAT_ORDER]
    for cat in ordered:
        names = sorted(grouped[cat])
        label = _CATEGORY_LABELS.get(cat, cat)
        lines.append(f"\n{label} ({len(names)}):")
        for n in names:
            impl = _IMPL_INDEX.get(n)
            impl_txt = f"{os.path.basename(impl[0])}:{impl[1]}" if impl else "(unknown)"
            reg = reg_lines.get(n)
            reg_txt = f"__init__.py:{reg}" if reg else "?"
            lines.append(
                f"  {n:<30} -> {impl_txt:<32} reg {reg_txt:<22} mcp:{'y' if _is_exposed(cat) else 'n'}  on:{'y' if _is_enabled(n) else 'n'}"
            )
    stale = _collect_stale_refs()
    if stale:
        lines.append("")
        lines.append(f"STALE REFERENCES ({len(stale)} names in docs/mocks not registered):")
        for tok, locs in sorted(stale.items())[:25]:
            lines.append(f"  {tok:<28} -> {', '.join(sorted(locs)[:3])}")
        if len(stale) > 25:
            lines.append(f"  ... and {len(stale) - 25} more")
    else:
        lines.append("\nSTALE REFERENCES: none")
    return "\n".join(lines)


def tool_anatomy(input_data=None) -> str:
    if isinstance(input_data, str):
        params = {"name": input_data}
    elif isinstance(input_data, dict):
        params = input_data
    else:
        params = {}
    name = params.get("name")
    names = params.get("names")
    show_config = bool(params.get("config", False))
    if isinstance(names, str):
        names = [names]
    targets = []
    if names:
        targets = [str(n) for n in names]
    elif name:
        targets = [str(name)]
    if targets:
        body = "\n\n".join(_deep_trace(t) for t in targets)
        if show_config:
            return _config_header() + "\n\n" + body
        return body
    return _inventory(category=params.get("category"))
