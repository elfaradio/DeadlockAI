from __future__ import annotations

from src.domain.models.banker import BankersAlgorithm


def test_bankers_safe_case() -> None:
    allocation = [[1, 0], [0, 1]]
    maximum = [[1, 1], [1, 1]]
    available = [1, 0]
    process_names = ["P1", "P2"]

    result = BankersAlgorithm.evaluate(allocation, maximum, available, process_names)
    assert result.safe is True
    assert len(result.safe_sequence) == 2


def test_bankers_unsafe_case() -> None:
    allocation = [[1, 0], [0, 1]]
    maximum = [[2, 1], [1, 2]]
    available = [0, 0]
    process_names = ["P1", "P2"]

    result = BankersAlgorithm.evaluate(allocation, maximum, available, process_names)
    assert result.safe is False
