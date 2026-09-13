"""Registry smoke: native + external descriptors load; version/skip/task work."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "codebase"))

from development.module_registry import (
    applicable_nodes, content_hash, list_native_modules, load_module,
    module_task_snippet, module_version,
)

EXT = "/home/manigupt/Hello/control-works/arcade_games/drift_racer"


def test_native_descriptor():
    assert "popula_dyn" in list_native_modules()
    spec = load_module("popula_dyn")
    assert spec["kind"] == "native_sim" and spec["topic"] == "popu_sim"
    assert isinstance(module_version(spec), str)


def test_external_descriptor():
    spec = load_module(EXT)
    assert spec["kind"] == "external"
    assert spec["topic"] == "controlworks_arcade_games"
    ver = module_version(spec)
    assert ver.startswith("ch@") and len(ver) == 15
    assert ver == "ch@" + content_hash(
        spec["lineage"]["patterns"], spec["_root"])  # deterministic
    task = module_task_snippet(spec)
    assert "arcade_games" in task["snippet"].lower()
    assert applicable_nodes(spec, ["hypothesis", "propose_architecture",
                                   "experiment"]) == ["hypothesis", "experiment"]


def test_missing_descriptor():
    try:
        load_module("/tmp/opencode/no_such_module_xyz")
    except FileNotFoundError:
        return
    raise AssertionError("expected FileNotFoundError")
