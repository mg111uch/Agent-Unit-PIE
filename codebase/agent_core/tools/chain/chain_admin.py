"""chain_admin: manage mined chains — list, approve (writes), delete, candidates.

Read-only mined chains auto-promote; chains with write steps are stored as
'pending' and only become live tools after an explicit approve here.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from agent_core.tools.chain.chain_store import chain_store
from agent_core.tools.chain.chain_miner import miner


def _register_spec(spec: Dict[str, Any]):
    try:
        from agent_core.tools import registry, tool_call
        from agent_core.tools.chain.chain_engine import make_chain_tool
        from agent_core.tools.chain.chain_spec import ChainSpec, Step
        from agent_core.tools.registry import CAT_CHAIN
        rebuilt = ChainSpec(
            name=spec["name"], category=spec["category"], description=spec["description"],
            params=spec.get("params", {}),
            steps=[Step(tool=s["tool"], args=s.get("args", {}), name=s.get("name", ""),
                        collect=s.get("collect", {}), optional=s.get("optional", False))
                   for s in spec.get("steps", [])],
            budget_tokens=spec.get("budget_tokens", 16000),
            step_cap_chars=spec.get("step_cap_chars", 8000),
        )
        if registry.has_tool(rebuilt.name):
            return
        registry.register(rebuilt.name, tool_call(make_chain_tool(rebuilt)),
                          description=rebuilt.description, params=rebuilt.params, category=CAT_CHAIN)
    except Exception as e:  # noqa: BLE001
        return f"Error registering: {e}"


def _line(row: Dict[str, Any]) -> str:
    steps = ", ".join(s["tool"] for s in row.get("steps", []))
    return (f"{row['name']}  [{row['status']} | {'RO' if row['read_only'] else 'WRITE'} | "
            f"{row['source']} | used {row['use_count']}]\n    {row['description']}\n    steps: {steps}")


def chain_admin(input_data) -> str:
    if isinstance(input_data, str):
        try:
            input_data = json.loads(input_data)
        except Exception:
            input_data = {}
    action = (input_data or {}).get("action", "list")
    name = (input_data or {}).get("name", "")

    if action == "list":
        rows = chain_store.list_specs()
        if not rows:
            return "No chains stored yet."
        return "Mined/handwritten chains:\n" + "\n\n".join(_line(r) for r in rows)

    if action == "candidates":
        rows = chain_store.list_candidates()
        if not rows:
            return "No mining candidates yet."
        lines = ["Mining candidates (repeated tool sequences):"]
        for r in rows:
            savings = f", ~{r.get('savings_est', 0)} tok saved" if r.get("savings_est") else ""
            lines.append(f"  {r['signature']}  x{r['occurrences']}{savings}")
        return "\n".join(lines)

    if action == "approve":
        if not name:
            return "Error: 'name' is required for approve."
        spec = chain_store.get_spec(name)
        if spec is None:
            return f"Error: no chain named '{name}'."
        chain_store.set_status(name, "approved")
        err = _register_spec(spec)
        if err:
            return f"Approved '{name}' (stored) but live registration failed: {err}"
        return f"Approved and registered '{name}' as a live tool."

    if action == "activate":
        if not name:
            return "Error: 'name' is required for activate."
        spec = chain_store.get_spec(name)
        if spec is None:
            return f"Error: no chain named '{name}'."
        chain_store.set_status(name, "approved")
        err = _register_spec(spec)
        if err:
            return f"Activated '{name}' (stored) but live registration failed: {err}"
        return f"Reactivated '{name}' as a live tool."

    if action == "delete":
        if not name:
            return "Error: 'name' is required for delete."
        if chain_store.delete_spec(name):
            return f"Deleted chain '{name}'."
        return f"Error: no chain named '{name}'."

    return (
        "chain_admin actions: list | candidates | approve (name=...) | activate (name=...) "
        "| delete (name=...). Read-only mined chains auto-promote; write chains need approve "
        "to go live; inactive mined chains can be reactivated."
    )


chain_admin_tool = chain_admin
