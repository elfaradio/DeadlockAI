from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProcessState(str, Enum):
    RUNNING = "Running"
    WAITING = "Waiting"
    BLOCKED = "Blocked"
    TERMINATED = "Terminated"


@dataclass
class Process:
    pid: str
    state: ProcessState = ProcessState.WAITING
