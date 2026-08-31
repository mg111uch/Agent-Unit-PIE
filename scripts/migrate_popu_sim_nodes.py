#!/usr/bin/env python3
"""
migrate_popu_sim_nodes.py

Migrates popu_sim topic nodes from verbose raw-data premises
to structured contradiction-friendly premises.

Usage:
    python scripts/migrate_popu_sim_nodes.py [--dry-run]
"""

import argparse
import json
import sys
import time

sys.path.insert(0, "codebase")

from kernel.persistence.db import kernel_db


def delete_topic_nodes(topic: str):
    nodes = kernel_db.load_semantic_nodes_by_topic(topic)
    deleted = []
    for n in nodes:
        kernel_db.conn.execute(
            "DELETE FROM semantic_nodes WHERE node_id = ?", (n["node_id"],)
        )
        deleted.append(n["node_id"])
    kernel_db.conn.execute(
        "DELETE FROM semantic_edges WHERE topic_id = ?", (topic,)
    )
    kernel_db.conn.commit()
    return deleted


def create_node(topic: str, name: str, premise: str, node_type: str = "argument") -> str:
    from kernel.memory.memory_engine import memory_engine
    node_id = f"argu_{topic}_{name.replace(' ', '_')}"
    node_data = {
        "node_id": node_id,
        "node_type": node_type,
        "title": name,
        "content": premise,
        "concepts": ["argument"],
        "tags": [topic],
        "metadata": {},
        "confidence": 1.0,
        "importance": 0.7,
        "created_at": time.time(),
        "updated_at": time.time(),
        "source_refs": [],
        "topic_id": topic,
    }
    memory_engine.save_object(
        memory_type="semantic",
        object_id=node_id,
        data=node_data,
    )
    return node_id


def create_edge(topic: str, source_node_id: str, target_node_id: str, relation: str) -> str:
    from kernel.memory.memory_engine import memory_engine
    edge_id = f"edge_{relation}_{source_node_id}_{target_node_id}"
    edge_data = {
        "edge_id": edge_id,
        "source_node_id": source_node_id,
        "target_node_id": target_node_id,
        "relation_type": relation,
        "weight": 1.0,
        "confidence": 1.0,
        "metadata": {"writer": "migration_script"},
        "created_at": time.time(),
        "topic_id": topic,
    }
    memory_engine.save_object(
        memory_type="semantic",
        object_id=edge_id,
        data=edge_data,
    )
    return edge_id


def main():
    parser = argparse.ArgumentParser(description="Migrate popu_sim nodes to structured premises")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be changed without writing")
    args = parser.parse_args()

    from modules.simulators.simulation_connector import SimulationConnector
    conn = SimulationConnector()

    print("=== Migration Plan ===\n")

    structured_premises = {}

    print("1. Nodes to DELETE:")
    nodes = kernel_db.load_semantic_nodes_by_topic("popu_sim")
    for n in nodes:
        print(f"   - {n['title']} ({n['node_id']})")

    print("\n2. Nodes to CREATE with structured premises:")

    structured_premises["Init"] = (
        "Initial seed node for popu_sim topic. "
        "Simulation topic for population dynamics experimentation."
    )
    print(f"   - Init (keep as-is)")

    run_basic_premise = conn.generate_structured_premise("run_basic")
    structured_premises["run_basic Findings"] = run_basic_premise
    print(f"   - run_basic Findings:")
    for line in run_basic_premise.split("\n")[:3]:
        print(f"       {line}")

    import os
    if os.path.exists(conn._resolve_run_path("run_policy_birth08") / "summary.json"):
        run08_premise = conn.generate_structured_premise("run_policy_birth08", "run_basic")
        structured_premises["run_policy_birth08 Findings"] = run08_premise
        print(f"   - run_policy_birth08 Findings:")
        for line in run08_premise.split("\n")[:3]:
            print(f"       {line}")

    if "run_policy_birth06 Findings" not in [n["title"] for n in nodes]:
        run06_premise = conn.generate_structured_premise("run_policy_birth06", "run_basic")
        structured_premises["run_policy_birth06 Findings"] = run06_premise
        print(f"   - run_policy_birth06 Findings (NEW from disk):")
        for line in run06_premise.split("\n")[:3]:
            print(f"       {line}")

    print("\n3. Contradicts edges to CREATE:")
    if "run_policy_birth06 Findings" in structured_premises and "run_policy_birth08 Findings" in structured_premises:
        print("   - run_policy_birth06 Findings contradicts run_policy_birth08 Findings")
        print("     (IMPROVED vs DEGRADED on same population metric)")
    elif "run_policy_birth06 Findings" in structured_premises:
        print("   - run_policy_birth06 Findings: no contradicts edge (run_policy_birth08 not in kernel)")

    if args.dry_run:
        print("\n[DRY RUN] No changes written.")
        return 0

    print("\n=== Executing Migration ===\n")

    print("Deleting existing nodes...")
    deleted = delete_topic_nodes("popu_sim")
    print(f"  Deleted {len(deleted)} nodes")

    print("Creating new nodes with structured premises...")
    node_ids = {}
    for name, premise in structured_premises.items():
        node_id = create_node("popu_sim", name, premise)
        node_ids[name] = node_id
        print(f"  Created: {name}")

    print("\nCreating contradicts edges...")
    if "run_policy_birth06 Findings" in node_ids and "run_policy_birth08 Findings" in node_ids:
        edge_id = create_edge(
            "popu_sim",
            node_ids["run_policy_birth06 Findings"],
            node_ids["run_policy_birth08 Findings"],
            "contradicts"
        )
        print(f"  Created contradicts edge: run_policy_birth06 -> run_policy_birth08")
    else:
        print(f"  Skipped contradicts edge: run_policy_birth06={('run_policy_birth06 Findings' in node_ids)}, run_policy_birth08={('run_policy_birth08 Findings' in node_ids)}")

    print("\nMigration complete!")

    print("\nVerifying:")
    nodes = kernel_db.load_semantic_nodes_by_topic("popu_sim")
    for n in nodes:
        print(f"  - {n['title']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
