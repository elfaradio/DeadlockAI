from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EdgeType(str, Enum):
    REQUEST = "request"
    ALLOCATION = "allocation"


@dataclass
class Edge:
    from_node: str
    to_node: str
    edge_type: EdgeType
