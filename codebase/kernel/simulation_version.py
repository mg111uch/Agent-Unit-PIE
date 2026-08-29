"""Phase 0 refactored: Per-simulator Git lineage — strictly isolated.

Single responsibility: version lifecycle per simulator.
All writes via kernel.persistence.db (one persistence path).
Fallback to file hash when not in git repo.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Any, Optional

from kernel.schemas.simulation_schema import concepts_for_changed_files
from kernel.utils.logger import get_child_logger

logger = get_child_logger("simulation_version")

DEFAULT_SIM = "popula_dyn"


def _db():
    from kernel.persistence.db import kernel_db
    return kernel_db


def current_code_hash(simulator: str = DEFAULT_SIM) -> str:
    try:
        from kernel.git_version import current_code_hash_fallback
        return current_code_hash_fallback()
    except Exception:
        return "unknown"


def current_git_commit(simulator: str = DEFAULT_SIM, short: bool = True) -> Optional[str]:
    try:
        from kernel.git_version import sim_commit
        return sim_commit(simulator, short=short)
    except Exception:
        return None


def get_current_version(simulator: str = DEFAULT_SIM) -> Optional[Dict[str, Any]]:
    return _db().load_latest_version(simulator=simulator)


def get_or_create_initial_version(simulator: str = DEFAULT_SIM) -> Dict[str, Any]:
    cur = get_current_version(simulator)
    if cur:
        return cur
    try:
        from kernel.git_version import is_git_repo, current_branch, git_commit_message, sim_commit
        from kernel.git_version import parent_commit as git_parent
        if is_git_repo():
            commit = sim_commit(simulator, short=True)
            if commit:
                par_raw = git_parent(commit)
                # prefix parent with simulator for isolation
                par = f"{simulator}@{par_raw}" if par_raw and not par_raw.startswith(f"{simulator}@") else par_raw
                branch = current_branch() or ""
                msg = git_commit_message(commit) if commit else ""
                vid = f"{simulator}@{commit}"
                _db().save_simulation_version(vid, par, commit, change_reason="initial", change_summary=msg or "bootstrap", affected_concepts=[], git_branch=branch, git_message=msg, simulator=simulator)
                logger.info(f"Created initial {simulator} git version {vid} branch={branch}")
                return _db().load_simulation_version(vid, simulator=simulator) or _db().load_simulation_version(vid)
    except Exception:
        pass
    h = current_code_hash(simulator)
    vid = f"V1_{h[:6]}"
    # prefix legacy fallback too for isolation
    vid_pref = f"{simulator}@{vid}" if not vid.startswith(f"{simulator}@") else vid
    _db().save_simulation_version(vid_pref, None, h, change_reason="initial", change_summary="bootstrap", affected_concepts=[], simulator=simulator)
    logger.info(f"Created initial {simulator} version {vid_pref}")
    return _db().load_simulation_version(vid_pref, simulator=simulator) or _db().load_simulation_version(vid_pref)


def sync_from_git(simulator: str = DEFAULT_SIM, change_reason: str = "git_sync") -> Dict[str, Any]:
    try:
        from kernel.git_version import is_git_repo, parent_commit, current_branch, git_commit_message, diff_sim_files, sim_commit
        if not is_git_repo():
            return get_or_create_initial_version(simulator)
        commit = sim_commit(simulator, short=True)
        if not commit:
            return get_or_create_initial_version(simulator)
        vid = f"{simulator}@{commit}"
        existing = _db().load_simulation_version(vid, simulator=simulator)
        if existing:
            return existing
        # also check without prefix legacy
        legacy = _db().load_simulation_version(commit, simulator=simulator)
        if legacy:
            return legacy
        par_raw = parent_commit(commit)
        par = f"{simulator}@{par_raw}" if par_raw and not par_raw.startswith(f"{simulator}@") else par_raw
        branch = current_branch() or ""
        msg = git_commit_message(commit)
        files = diff_sim_files(simulator, par_raw, commit) if par_raw else []
        concepts = concepts_for_changed_files(files)
        _db().save_simulation_version(vid, par, commit, change_reason=change_reason, change_summary=f"[{branch}] {msg}", affected_concepts=concepts, git_branch=branch, git_message=msg, simulator=simulator)
        logger.info(f"Synced {simulator} git version {vid} parent={par} branch={branch} concepts={concepts}")
        # Phase 2: auto-invalidate stale findings for this simulator
        try:
            from kernel.validity import mark_stale_findings
            if concepts:
                mark_stale_findings(simulator, vid)
        except Exception as e:
            logger.warning(f"validity mark failed for {simulator} {vid}: {e}")
        return _db().load_simulation_version(vid, simulator=simulator) or _db().load_simulation_version(vid)
    except Exception as e:
        logger.warning(f"sync_from_git {simulator} failed: {e}")
        return get_or_create_initial_version(simulator)


def bump_version(changed_files: List[str], change_reason: str = "", change_summary: str = "", simulator: str = DEFAULT_SIM) -> Dict[str, Any]:
    try:
        from kernel.git_version import is_git_repo
        if is_git_repo():
            return sync_from_git(simulator, change_reason or "bump_version")
    except Exception:
        pass
    parent = get_or_create_initial_version(simulator)
    h = current_code_hash(simulator)
    if h == parent.get("code_hash") and not changed_files:
        return parent
    concepts = concepts_for_changed_files(changed_files)
    n = len(_db().load_all_simulation_versions(simulator=simulator)) + 1
    vid = f"V{n}_{h[:6]}"
    vid_pref = f"{simulator}@{vid}"
    _db().save_simulation_version(vid_pref, parent["version_id"], h, change_reason or "code_change", change_summary or f"files:{','.join(changed_files[:3])}", affected_concepts=concepts, simulator=simulator)
    logger.info(f"Bumped {simulator} {parent['version_id']} -> {vid_pref} concepts={concepts}")
    try:
        if concepts:
            from kernel.validity import mark_stale_findings
            mark_stale_findings(simulator, vid_pref)
    except Exception as e:
        logger.warning(f"validity mark failed for {simulator} {vid_pref}: {e}")
    return _db().load_simulation_version(vid_pref, simulator=simulator) or _db().load_simulation_version(vid_pref)


def list_lineage(version_id: Optional[str] = None, simulator: Optional[str] = None) -> List[Dict[str, Any]]:
    all_v = _db().load_all_simulation_versions(simulator=simulator)
    if not version_id:
        return all_v
    by_id = {v["version_id"]: v for v in all_v}
    out: List[Dict[str, Any]] = []
    cur = by_id.get(version_id)
    while cur:
        out.append(cur)
        cur = by_id.get(cur.get("parent_version_id") or "")
    return list(reversed(out))


def is_compatible(find_version_id: str, query_version_id: str, simulator: Optional[str] = None) -> bool:
    if not find_version_id or not query_version_id:
        return True
    if find_version_id == query_version_id:
        return True
    if find_version_id.startswith("V"):
        return True
    lineage = list_lineage(query_version_id, simulator=simulator)
    ids = {v["version_id"] for v in lineage}
    return find_version_id in ids


def affected_by(find_concepts: List[str], version_concepts: List[str]) -> bool:
    if not find_concepts or not version_concepts:
        return False
    return bool(set(find_concepts) & set(version_concepts))


def validity_for_node(node) -> Dict[str, Any]:
    md = getattr(node, "metadata", {}) or {}
    if isinstance(md.get("validity"), dict):
        return md["validity"]
    obs = md.get("observation", {})
    if isinstance(obs, dict) and obs.get("version_id"):
        return {"valid_for_version": obs["version_id"], "status": "ACTIVE", "simulator": obs.get("simulator", DEFAULT_SIM)}
    return {"valid_for_version": "V0", "status": "ACTIVE", "simulator": DEFAULT_SIM}
