from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np


@dataclass
class BankerResult:
    safe: bool
    safe_sequence: List[str]
    need_matrix: List[List[int]]
    work_trace: List[List[int]]
    explanation: str


class BankersAlgorithm:
    """Classic Banker's safety algorithm implementation in Domain layer."""

    @staticmethod
    def evaluate(
        allocation: List[List[int]],
        maximum: List[List[int]],
        available: List[int],
        process_names: List[str],
    ) -> BankerResult:
        alloc = np.array(allocation, dtype=int)
        maxm = np.array(maximum, dtype=int)
        avail = np.array(available, dtype=int)

        if alloc.shape != maxm.shape:
            raise ValueError("Allocation and Maximum matrices must have same dimensions")
        if alloc.shape[0] != len(process_names):
            raise ValueError("Process names count must match matrix rows")
        if alloc.shape[1] != len(avail):
            raise ValueError("Available matrix width must match resource columns")

        need = maxm - alloc
        if np.any(need < 0):
            raise ValueError("Maximum matrix cannot be smaller than allocation matrix")

        finish = [False] * alloc.shape[0]
        work = avail.copy()
        safe_sequence: List[str] = []
        work_trace: List[List[int]] = [work.astype(int).tolist()]

        made_progress = True
        while len(safe_sequence) < alloc.shape[0] and made_progress:
            made_progress = False
            for i in range(alloc.shape[0]):
                if finish[i]:
                    continue
                if np.all(need[i] <= work):
                    work += alloc[i]
                    finish[i] = True
                    safe_sequence.append(process_names[i])
                    work_trace.append(work.astype(int).tolist())
                    made_progress = True

        safe = len(safe_sequence) == alloc.shape[0]
        if safe:
            explanation = (
                "System is in a SAFE state. All processes can finish in order: "
                + " -> ".join(safe_sequence)
            )
        else:
            remaining = [process_names[i] for i, done in enumerate(finish) if not done]
            explanation = (
                "System is in an UNSAFE state. Processes that could not be satisfied: "
                + ", ".join(remaining)
            )

        return BankerResult(
            safe=safe,
            safe_sequence=safe_sequence,
            need_matrix=need.astype(int).tolist(),
            work_trace=work_trace,
            explanation=explanation,
        )
