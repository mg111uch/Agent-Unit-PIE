#!/usr/bin/env python3
"""Dead code candidate detector — PASSIVE REPORT GENERATOR ONLY.

This tool NEVER deletes or modifies code. It only parses files with the stdlib
`ast` module and prints a report of dead-code candidates, grouped by category:

  imports      : imported names never used in the file (skips __init__.py
                 re-exports unless --check-init-imports)
  unreachable  : statements after an unconditional return/raise/break/continue,
                 and bodies of `if False:` / `while False:` (or `else` of
                 `if True:`)
  locals       : names stored but never read within a function
  unreferenced : top-level functions/classes never referenced anywhere in the
                 codebase (imports, Name loads, string-dispatch and __all__
                 all count as references)

Usage:
  conda run --no-capture-output -n myenv python codebase/agent_tools/dead_code_detector.py
  conda run --no-capture-output -n myenv python codebase/agent_tools/dead_code_detector.py --category unreferenced imports
  conda run --no-capture-output -n myenv python codebase/agent_tools/dead_code_detector.py --json --output report.json

Example run against the codebase (default --root codebase, defaults otherwise):
  conda run --no-capture-output -n myenv python codebase/agent_tools/dead_code_detector.py

  Expected output (representative hits, capped at --max-per-file per category):

    codebase/tool_client.py
      [imports]
        L17: import json                          # never used in file
        L23: from agent_core.tools.code_rag import _get_rag   # never used in file

    codebase/storage/unit_storage.py
      [unreferenced]
        L49: UnitStorage   class UnitStorage:    # never referenced anywhere

    codebase/sloperator/post_composer.py
      [locals]
        L156: prompt_file_path   # stored but never read (only referenced in comments)

    ============================================================
    files scanned:    350
    unused-imports:   136
    unreachable:      0
    unused-locals:    20
    unreferenced:     317

  All numbers above are candidates for human review, never auto-removed.
"""

from __future__ import annotations

import argparse
import ast
import json
import os
from collections import Counter, defaultdict

DEFAULT_ROOT = "/home/manigupt/Hello/Agentic_Unit_PIE/codebase"
DEFAULT_IGNORE_DIRS = {".git", "__pycache__", "node_modules", "dist", "build", ".venv", "env"}
DEFAULT_IGNORE_FILES = set()

CATEGORIES = {
    "imports": "unused-imports",
    "unreachable": "unreachable",
    "locals": "unused-locals",
    "unreferenced": "unreferenced",
}


def _iter_files(root, extensions, ignore_dirs, ignore_files):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for fn in sorted(filenames):
            if fn in ignore_files:
                continue
            if os.path.splitext(fn)[1].lower() in extensions:
                yield os.path.join(dirpath, fn)


def _parse_file(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return ast.parse(f.read())


def _statement_lists(node):
    yield node.body
    for n in ast.walk(node):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.With)):
            yield n.body
        elif isinstance(n, (ast.If, ast.For, ast.While)):
            yield n.body
            yield n.orelse
        elif isinstance(n, ast.Try):
            yield n.body
            yield n.orelse
            yield n.finalbody
            for h in n.handlers:
                yield h.body


def _analyze_file(tree):
    """Return per-file reference data used by the index and the categories."""
    loads = Counter()
    strings = set()
    dyn_strings = set()
    imports = []
    all_entries = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            loads[node.id] += 1
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.isidentifier():
            strings.add(node.value)
        elif isinstance(node, ast.Import):
            for a in node.names:
                imports.append((node.lineno, "import " + a.name, a.asname or a.name.split(".")[0]))
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                if a.name != "*":
                    imports.append(
                        (node.lineno, "from " + (node.module or "") + " import " + a.name, a.asname or a.name)
                    )
        elif isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            dyn_strings.add(node.slice.value)
        elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in ("getattr", "setattr", "delattr", "globals", "locals", "vars")):
            for a in node.args:
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    dyn_strings.add(a.value)
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "__all__"):
            try:
                value = ast.literal_eval(node.value)
                if isinstance(value, list):
                    all_entries = {e for e in value if isinstance(e, str)}
            except (ValueError, SyntaxError):
                pass
    return {"loads": loads, "strings": strings, "dyn_strings": dyn_strings, "imports": imports, "all": all_entries}


def _build_index(infos):
    global_loads = Counter()
    global_strings = set()
    global_dyn_strings = set()
    global_import_bindings = set()
    per_file = {}
    for path, tree in infos:
        data = _analyze_file(tree)
        per_file[path] = data
        global_loads.update(data["loads"])
        global_strings |= data["strings"]
        global_dyn_strings |= data["dyn_strings"]
        for _, _, bind in data["imports"]:
            global_import_bindings.add(bind)
    return per_file, global_loads, global_strings, global_dyn_strings, global_import_bindings


def _unused_imports(data, path, check_init_imports):
    if not check_init_imports and os.path.basename(path) == "__init__.py":
        return []
    used = set(data["loads"]) | data["strings"] | data["all"]
    items = []
    for lineno, text, bind in data["imports"]:
        if text.startswith("from __future__ import"):
            continue
        if bind not in used:
            items.append((lineno, text, "never used in file"))
    return items


def _unreachable(tree):
    items = []
    for block in _statement_lists(tree):
        exited = False
        for st in block:
            if exited:
                items.append(st.lineno)
            elif isinstance(st, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                exited = True
    for node in ast.walk(tree):
        if (isinstance(node, (ast.If, ast.While))
                and isinstance(node.test, ast.Constant) and isinstance(node.test.value, bool)):
            if node.test.value is False:
                for st in node.body:
                    items.append(st.lineno)
            elif node.test.value is True and isinstance(node, ast.If):
                for st in node.orelse:
                    items.append(st.lineno)
    return sorted(set(items))


def _unused_locals(tree):
    found = {}

    def own_scope_stores(fn):
        for child in ast.iter_child_nodes(fn):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda,
                                  ast.ClassDef, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                continue
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                found.setdefault(child.id, child.lineno)
            else:
                own_scope_stores(child)

    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        loads = set()
        aug = set()
        targets = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                loads.add(node.id)
            elif isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Name):
                aug.add(node.target.id)
            elif isinstance(node, (ast.For, ast.AsyncFor)):
                _collect_names(node.target, targets)
            elif isinstance(node, ast.With):
                for item in node.items:
                    if item.optional_vars is not None:
                        _collect_names(item.optional_vars, targets)
        own_scope_stores(fn)
        for name in list(found):
            if (name not in loads and name not in aug and name not in targets
                    and not name.startswith("_")):
                continue
            found.pop(name, None)
    return sorted((lineno, name) for name, lineno in found.items())


def _collect_names(node, out):
    if isinstance(node, ast.Name):
        out.add(node.id)
    else:
        for child in ast.iter_child_nodes(node):
            _collect_names(child, out)


def _unreferenced(infos, per_file, global_loads, global_dyn_strings, global_import_bindings):
    items = []
    for path, tree in infos:
        data = per_file[path]
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            name = node.name
            if name in data["all"] or name in global_import_bindings or name in global_dyn_strings:
                continue
            if global_loads[name] > 0:
                continue
            items.append((path, node.lineno, name, "never referenced anywhere"))
    return items


def _render_item(text, width=60):
    return text if len(text) <= width else text[: width - 3] + "..."


def main():
    parser = argparse.ArgumentParser(
        description="Passive dead-code candidate report generator. Never modifies or deletes code.",
    )
    parser.add_argument("--root", default=DEFAULT_ROOT, help=f"Root dir to scan (default: {DEFAULT_ROOT})")
    parser.add_argument("--extensions", nargs="+", default=[".py"], help="File extensions (default: .py)")
    parser.add_argument("--ignore-dirs", nargs="+", default=sorted(DEFAULT_IGNORE_DIRS))
    parser.add_argument("--ignore-files", nargs="+", default=sorted(DEFAULT_IGNORE_FILES))
    parser.add_argument("--category", nargs="+", choices=list(CATEGORIES) + ["all"], default=["all"],
                        help="Categories to check (default: all)")
    parser.add_argument("--max-per-file", type=int, default=20, help="Cap hits per category per file (default: 20)")
    parser.add_argument("--check-init-imports", action="store_true", help="Also flag unused imports in __init__.py")
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument("--output", help="Write JSON report to file")
    parser.add_argument("--no-code", action="store_true", help="Omit code excerpts")
    args = parser.parse_args()

    if "all" in args.category:
        enabled = set(CATEGORIES)
    else:
        enabled = set(args.category)

    paths = list(_iter_files(args.root, set(args.extensions), set(args.ignore_dirs), set(args.ignore_files)))
    infos = []
    for path in paths:
        try:
            infos.append((path, _parse_file(path)))
        except (SyntaxError, ValueError):
            continue

    per_file, global_loads, global_strings, global_dyn_strings, global_import_bindings = _build_index(infos)
    unreferenced = _unreferenced(infos, per_file, global_loads, global_dyn_strings, global_import_bindings)
    unreferenced_by_path = defaultdict(list)
    for path, lineno, name, reason in unreferenced:
        unreferenced_by_path[path].append((lineno, name, reason))

    report = defaultdict(lambda: defaultdict(list))
    counts = Counter()
    for path, tree in infos:
        data = per_file[path]
        code_lines = []
        if not args.no_code:
            with open(path, encoding="utf-8", errors="replace") as f:
                code_lines = f.read().splitlines()

        def add(cat, lineno, name, reason, text=None):
            if cat not in enabled:
                return
            if len(report[path][cat]) >= args.max_per_file:
                return
            if text is None:
                text = code_lines[lineno - 1].strip() if code_lines else ""
            report[path][cat].append({"line": lineno, "name": name, "reason": reason, "code": text})
            counts[cat] += 1

        if "imports" in enabled:
            for lineno, text, reason in _unused_imports(data, path, args.check_init_imports):
                add("imports", lineno, text, reason)
        if "unreachable" in enabled:
            for lineno in _unreachable(tree):
                add("unreachable", lineno, "<statement>", "unreachable code")
        if "locals" in enabled:
            for lineno, name in _unused_locals(tree):
                add("locals", lineno, name, "stored but never read")
        for lineno, name, reason in unreferenced_by_path.get(path, []):
            add("unreferenced", lineno, name, reason)

    print("=" * 70)
    print("Dead code candidates (report only — nothing is removed)")
    print("=" * 70)
    if args.no_code:
        print("(code excerpts suppressed with --no-code)")
    for path in sorted(report):
        print(f"\n{path}")
        for cat in CATEGORIES:
            items = report[path].get(cat)
            if not items:
                continue
            print(f"  [{cat}]")
            for it in items:
                excerpt = f"  {_render_item(it['code'])}" if it["code"] else ""
                print(f"    L{it['line']}: {it['name']}{excerpt}   # {it['reason']}")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"files scanned:    {len(infos)}")
    for cat in CATEGORIES:
        print(f"{CATEGORIES[cat]:<18}{counts[cat]:>6}")
    print(f"{'total (reported)':<18}{sum(counts.values()):>6}")

    if args.json or args.output:
        payload = {
            "root": args.root,
            "note": "passive report only; no code was modified or deleted",
            "files": {p: dict(g) for p, g in report.items()},
            "summary": dict(counts),
        }
        data = json.dumps(payload, indent=2)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(data + "\n")
            print(f"\nReport written to {args.output}")
        if args.json:
            print(data)


if __name__ == "__main__":
    main()
