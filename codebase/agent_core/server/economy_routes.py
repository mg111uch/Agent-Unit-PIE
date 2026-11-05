"""Human approval queue + customer portal endpoints.

Money-adjacent actions are human-JWT only. The only public surface is the
magic-link portal, where the unguessable token is the credential.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import Body, Depends, HTTPException
from fastapi.responses import FileResponse

from agent_core.server import app
from agent_core.server.auth import require_auth
from modules.economy import approval_store, portal

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"


def _public(proposal: dict, token: str) -> dict:
    out = {k: v for k, v in (proposal or {}).items()
           if k not in ("deliverable_path", "request")}
    out["download_available"] = portal.deliverable(token) is not None
    return out


# --- approval inbox ------------------------------------------------------
@app.get("/api/economy/approvals")
def list_approvals(status: str = "pending",
                   user: dict = Depends(require_auth)):
    return {"items": approval_store.list_items(status),
            "counts": approval_store.counts(), "actor": user.get("username")}


@app.post("/api/economy/approvals")
def queue_approval(payload: dict = Body(...),
                   user: dict = Depends(require_auth)):
    if not payload.get("action"):
        raise HTTPException(status_code=400, detail="action is required")
    payload.setdefault("requested_by", user.get("username") or "agent")
    return approval_store.save(payload)


@app.post("/api/economy/approvals/{item_id}/decide")
def decide_approval(item_id: str, payload: dict = Body(...),
                    user: dict = Depends(require_auth)):
    actor = user.get("username") or user.get("id") or "human"
    out = approval_store.decide(item_id, actor,
                                payload.get("decision", "approve"),
                                payload.get("reason", ""))
    if out.get("error"):
        raise HTTPException(status_code=409, detail=out["error"])
    return out


# --- proposals (operator) ------------------------------------------------
@app.get("/api/economy/proposals")
def list_proposals(user: dict = Depends(require_auth)):
    return {"items": portal.list_all()}


@app.post("/api/economy/proposals")
def create_proposal(payload: dict = Body(...),
                    user: dict = Depends(require_auth)):
    out = portal.create(payload.get("customer", ""),
                        payload.get("title", ""),
                        float(payload.get("price") or 0),
                        payload.get("deliverable_path", ""),
                        payload.get("request") or {})
    if out.get("error"):
        raise HTTPException(status_code=400, detail=out["error"])
    return out


@app.post("/api/economy/proposals/{proposal_id}/paid")
def mark_paid(proposal_id: str, payload: dict = Body(...),
              user: dict = Depends(require_auth)):
    out = portal.mark_paid(proposal_id, payload.get("reference", ""),
                           user.get("username") or "human")
    if out.get("error"):
        raise HTTPException(status_code=409, detail=out["error"])
    return out


# --- customer portal (token is the credential) ---------------------------
@app.get("/api/portal/{token}")
def portal_view(token: str):
    proposal = portal.get(token)
    if not proposal:
        raise HTTPException(status_code=404, detail="unknown or expired link")
    return _public(proposal, token)


@app.post("/api/portal/{token}/accept")
def portal_accept(token: str, payload: dict = Body(default={})):
    out = portal.accept(token, payload.get("actor") or "customer")
    if out.get("error"):
        raise HTTPException(status_code=409, detail=out["error"])
    return {**out, "proposal": _public(out["proposal"], token)}


@app.get("/api/portal/{token}/download")
def portal_download(token: str):
    if not portal.get(token):
        raise HTTPException(status_code=404, detail="unknown or expired link")
    path = portal.deliverable(token)
    if not path:
        raise HTTPException(status_code=404, detail="no deliverable yet")
    return FileResponse(path, filename=path.name)


@app.get("/portal/{token}", include_in_schema=False)
def portal_page(token: str):
    page = FRONTEND / "portal.html"
    if not page.is_file():
        raise HTTPException(status_code=404, detail="portal page missing")
    return FileResponse(page)


@app.get("/approvals", include_in_schema=False)
def approvals_page():
    page = FRONTEND / "approvals.html"
    if not page.is_file():
        raise HTTPException(status_code=404, detail="approvals page missing")
    return FileResponse(page)
