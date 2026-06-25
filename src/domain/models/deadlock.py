from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import networkx as nx


@dataclass
class DeadlockResult:
    is_deadlocked: bool
    cycle: List[str]
    processes: List[str]
    resources: List[str]


def detect_deadlock(graph: nx.DiGraph) -> DeadlockResult:
    """Detect deadlock by checking for directed cycles in the Resource Allocation Graph (RAG)."""
    try:
        cycle_edges = nx.find_cycle(graph, orientation="original")
    except nx.NetworkXNoCycle:
        return DeadlockResult(False, [], [], [])

    cycle_nodes = _cycle_nodes_in_order(cycle_edges)
    processes = sorted({node for node in cycle_nodes if str(node).startswith("P")})
    resources = sorted({node for node in cycle_nodes if str(node).startswith("R")})

    return DeadlockResult(True, cycle_nodes, processes, resources)


def _cycle_nodes_in_order(cycle_edges: Sequence[tuple]) -> List[str]:
    if not cycle_edges:
        return []
    nodes: List[str] = [str(cycle_edges[0][0]), str(cycle_edges[0][1])]
    for edge in cycle_edges[1:]:
        nodes.append(str(edge[1]))
    if nodes[0] == nodes[-1]:
        return nodes
    nodes.append(nodes[0])
    return nodes
