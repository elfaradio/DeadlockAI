from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Resource:
    rid: str
    total_instances: int
    allocated_instances: int = 0

    @property
    def available_instances(self) -> int:
        return self.total_instances - self.allocated_instances
