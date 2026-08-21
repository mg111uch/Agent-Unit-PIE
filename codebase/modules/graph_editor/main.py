import json
import os
import re

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

BASE_PATH = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(BASE_PATH, "..", "..", ".."))
WORKFLOWS_DIR = os.path.join(WORKSPACE_ROOT, "data", "workflows")

app = FastAPI(title="GraphEditor")


class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        resp = await super().get_response(path, scope)
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return resp


app.mount("/static", NoCacheStaticFiles(directory=BASE_PATH), name="static")


@app.get("/")
async def root():
    resp = FileResponse(os.path.join(BASE_PATH, "index.html"))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp


def find_save_target(name: str) -> str:
    """Resolve where to read/write a graph.

    Preference order: absolute path → an existing file with this basename in the
    workspace (preferring data/workflows/, then data/) → path relative to CWD →
    CWD-relative fallback.
    """
    raw = str(name).strip()
    if os.path.isabs(raw):
        return raw
    name = os.path.basename(raw)
    workspace = WORKSPACE_ROOT
    skip = {".git", "__pycache__", "node_modules", "venv", ".venv", "env",
            "chroma_db", "atlas_output", "logs", "build", "dist", ".cache",
            ".conda", "site-packages", "kb"}
    workflow_match = data_match = other_match = None
    for root, dirs, files in os.walk(workspace):
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
        if name in files:
            match = os.path.join(root, name)
            rel = os.path.relpath(match, workspace)
            if rel.startswith(os.path.join("data", "workflows", "")):
                return match
            if rel.startswith(os.path.join("data", "")) and data_match is None:
                data_match = match
            if other_match is None:
                other_match = match
    if data_match:
        return data_match
    if other_match:
        return other_match
    rel = os.path.join(os.getcwd(), name)
    if os.path.exists(rel):
        return rel
    return rel


@app.get("/api/graphs")
async def list_graphs():
    try:
        files = sorted(f for f in os.listdir(WORKFLOWS_DIR) if f.endswith(".json"))
        return {"ok": True, "graphs": files}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/graph")
async def get_graph(path: str = ""):
    name = str(path).strip()
    if not name:
        return {"ok": False, "error": "No graph path provided"}
    try:
        target = find_save_target(name)
        if not os.path.isfile(target):
            return {"ok": False, "error": f"Not found: {name}"}
        with open(target) as f:
            return json.load(f)
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _slugify(text: str) -> str:
    s = text.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def _parse_md_headings(text: str):
    headings = []
    for i, line in enumerate(text.splitlines(), start=1):
        m = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            headings.append({"level": level, "text": title, "slug": _slugify(title), "line": i})
    return headings


def _resolve_md_path(name: str) -> str:
    raw = str(name).strip()
    if not raw:
        return ""
    file_part = raw.split("#", 1)[0].strip()
    if os.path.isabs(file_part):
        return file_part
    # exact relative path under workspace wins
    cand = os.path.join(WORKSPACE_ROOT, file_part)
    if os.path.isfile(cand):
        return cand
    # prefer data/workflows like find_save_target for graphs
    base = os.path.basename(file_part)
    wf_cand = os.path.join(WORKFLOWS_DIR, base)
    if os.path.isfile(wf_cand):
        return wf_cand
    # basename search fallback (like find_save_target but for md)
    skip = {".git", "__pycache__", "node_modules", "venv", ".venv", "env",
            "chroma_db", "atlas_output", "logs", "build", "dist", ".cache",
            ".conda", "site-packages", "kb"}
    for root, dirs, files in os.walk(WORKSPACE_ROOT):
        dirs[:] = [d for d in dirs if d not in skip and not d.startswith(".")]
        if base in files and base.lower().endswith(".md"):
            return os.path.join(root, base)
    return wf_cand if os.path.isfile(wf_cand) else cand


@app.get("/api/md_files")
async def list_md_files():
    try:
        files = sorted(f for f in os.listdir(WORKFLOWS_DIR) if f.lower().endswith(".md"))
        return {"ok": True, "files": files}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/md_sections")
async def md_sections(path: str = ""):
    name = str(path).strip().split("#", 1)[0].strip()
    if not name:
        return {"ok": False, "error": "No path provided"}
    try:
        target = _resolve_md_path(name)
        if not os.path.isfile(target):
            return {"ok": False, "error": f"Not found: {name}"}
        text = open(target, encoding="utf-8", errors="replace").read()
        headings = _parse_md_headings(text)
        rel = os.path.relpath(target, WORKSPACE_ROOT)
        return {"ok": True, "file": rel, "headings": headings}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.get("/api/md_content")
async def md_content(path: str = ""):
    raw = str(path).strip()
    if not raw:
        return {"ok": False, "error": "No path provided"}
    try:
        file_part, _, anchor = raw.partition("#")
        target = _resolve_md_path(file_part.strip())
        if not os.path.isfile(target):
            return {"ok": False, "error": f"Not found: {file_part}"}
        text = open(target, encoding="utf-8", errors="replace").read()
        headings = _parse_md_headings(text)
        lines = text.splitlines()
        # if anchor given, slice section by heading level
        if anchor.strip():
            slug = _slugify(anchor.strip())
            # find heading matching slug or raw anchor text
            idx = -1
            target_level = None
            for h in headings:
                if h["slug"] == slug or h["text"].lower() == anchor.strip().lower():
                    idx = h["line"] - 1
                    target_level = h["level"]
                    break
            if idx == -1:
                # fallback: search line text contains anchor
                for h in headings:
                    if slug in h["slug"]:
                        idx = h["line"] - 1
                        target_level = h["level"]
                        break
            if idx != -1:
                start = idx
                end = len(lines)
                for h in headings:
                    if h["line"] - 1 > start and h["level"] <= target_level:
                        end = h["line"] - 1
                        break
                section = "\n".join(lines[start:end]).strip()
                rel = os.path.relpath(target, WORKSPACE_ROOT)
                return {"ok": True, "file": rel, "anchor": anchor.strip(), "slug": slug, "content": section, "headings": headings}
        rel = os.path.relpath(target, WORKSPACE_ROOT)
        return {"ok": True, "file": rel, "content": text, "headings": headings}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/api/save")
async def save_graph(body: dict):
    path = str(body.get("path", "")).strip()
    if not path:
        return {"ok": False, "error": "No file path provided"}
    data = body.get("data")
    if not isinstance(data, dict) or "nodes" not in data or "edges" not in data:
        return {"ok": False, "error": "Expected {\"nodes\":[...],\"edges\":[...]}"}
    try:
        target = find_save_target(path)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w") as f:
            json.dump(data, f, indent=2)
        return {"ok": True, "path": target}
    except Exception as e:
        return {"ok": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn

    print("GraphEditor server starting at http://localhost:8004", flush=True)
    uvicorn.run("main:app", host="0.0.0.0", port=8004, reload=False)