from __future__ import annotations

from typing import List
from src.domain.models.banker import BankerResult, BankersAlgorithm


class BankersService:

    @staticmethod
    def evaluate(
        allocation: List[List[int]],
        maximum: List[List[int]],
        available: List[int],
        process_names: List[str],
    ) -> BankerResult:
        """Evaluate the safety of the state using the Banker's Algorithm."""
        return BankersAlgorithm.evaluate(
            allocation, maximum, available, process_names
        )
