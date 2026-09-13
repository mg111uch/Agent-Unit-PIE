"""Module registry — native sims + external dirs as loop citizens.

Each module keeps a ``module.json`` in its own dir; the research loop and
kernel load it at runtime for topic, task source, lineage strategy,
commands, metric gates and node bypasses. No central registry file.
"""
from __future__ import annotations
import glob
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]
NATIVE_SIMS = WORKSPACE_ROOT / "codebase" / "modules" / "simulators"
DESCRIPTOR = "module.json"
KINDS = ("native_sim", "external")
REQUIRED = ("name", "kind", "topic")


def _load_json(path: Path) -> Dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must hold a JSON object")
    return data


def _resolve_task_file(spec: Dict[str, Any]) -> Path:
    raw = (spec.get("task_source") or {}).get("file", "")
    p = Path(raw)
    if not p.is_absolute():
        p = WORKSPACE_ROOT / raw
    return p


def load_module(ref: str) -> Dict[str, Any]:
    """Load a descriptor by native sim name or absolute module path."""
    if "/" in ref or ref.startswith("~"):
        root = Path(ref).expanduser().resolve()
        path = root / DESCRIPTOR
    else:
        root = (NATIVE_SIMS / ref).resolve()
        path = root / DESCRIPTOR
    if not path.is_file():
        raise FileNotFoundError(f"no {DESCRIPTOR} at {path}")
    spec = _load_json(path)
    for key in REQUIRED:
        if not spec.get(key):
            raise ValueError(f"{path} missing required key '{key}'")
    if spec["kind"] not in KINDS:
        raise ValueError(f"{path} kind must be one of {KINDS}")
    spec["_root"] = str(root)
    spec["_descriptor"] = str(path)
    return spec


def list_native_modules() -> List[str]:
    """Native sim names that ship a descriptor."""
    if not NATIVE_SIMS.is_dir():
        return []
    return sorted(p.name for p in NATIVE_SIMS.iterdir()
                  if (p / DESCRIPTOR).is_file())


def content_hash(patterns: List[str], root: str) -> str:
    """Content-hash lineage for zero-git externals (12 hex chars)."""
    h = hashlib.sha256()
    files: List[str] = []
    for pat in patterns or ["**/*.py"]:
        files.extend(glob.glob(str(Path(root) / pat), recursive=True))
    for fp in sorted(set(files)):
        p = Path(fp)
        if p.is_file():
            h.update(str(p.relative_to(root)).encode())
            h.update(p.read_bytes())
    return h.hexdigest()[:12]


def module_version(spec: Dict[str, Any]) -> str:
    """Native: sim@commit. External: ch@contenthash."""
    if spec.get("kind") == "native_sim":
        try:
            from kernel.git_version import sim_commit
            name = spec.get("simulator") or spec["name"]
            return sim_commit(name, short=True) or "unknown"
        except Exception:
            return "unknown"
    lin = spec.get("lineage") or {}
    digest = content_hash(lin.get("patterns", ["**/*.py"]), spec["_root"])
    return f"ch@{digest}"


def module_task_snippet(spec: Dict[str, Any], max_chars: int = 600) -> Dict[str, Any]:
    """Task source: file + section/marker + snippet (best effort)."""
    task = spec.get("task_source") or {}
    out: Dict[str, Any] = {"file": task.get("file", ""),
                           "section": task.get("section", ""),
                           "marker": task.get("marker", ""),
                           "snippet": ""}
    try:
        text = _resolve_task_file(spec).read_text(encoding="utf-8")
    except Exception:
        return out
    anchor = task.get("section") or task.get("marker") or ""
    if anchor and anchor in text:
        text = text.split(anchor, 1)[1]
    out["snippet"] = text.strip()[:max_chars]
    return out


def module_topic_nodes(spec: Dict[str, Any]) -> Dict[str, Any]:
    """Kernel memory summary for the module topic (read-only, best effort)."""
    topic = spec.get("topic", "")
    try:
        from modules.argu_god.engine.topic_store import hydrate, export_graph
        hydrate()
        nodes = (export_graph(topic) or {}).get("nodes") or []
        decisions = [n.get("name", "") for n in nodes
                     if isinstance(n, dict) and n.get("side") == "decision"]
        return {"topic": topic, "nodes": len(nodes), "decisions": decisions[-8:]}
    except Exception as e:
        return {"topic": topic, "error": str(e)}


def applicable_nodes(spec: Dict[str, Any], allowed: List[str]) -> List[str]:
    """Engine-allowed nodes minus descriptor bypasses (no engine change)."""
    skip = set(spec.get("skip_nodes") or [])
    return [n for n in (allowed or []) if n not in skip]
