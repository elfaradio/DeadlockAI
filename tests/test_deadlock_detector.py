from __future__ import annotations

import networkx as nx
from src.domain.models.deadlock import detect_deadlock


def test_detect_deadlock_true() -> None:
    graph = nx.DiGraph()
    graph.add_edges_from([
        ("P1", "R2"),
        ("R2", "P2"),
        ("P2", "R1"),
        ("R1", "P1"),
    ])
    result = detect_deadlock(graph)
    assert result.is_deadlocked is True
    assert "P1" in result.processes
    assert "R1" in result.resources


def test_detect_deadlock_false() -> None:
    graph = nx.DiGraph()
    graph.add_edges_from([
        ("R1", "P1"),
        ("P2", "R2"),
    ])
    result = detect_deadlock(graph)
    assert result.is_deadlocked is False
    assert result.cycle == []
