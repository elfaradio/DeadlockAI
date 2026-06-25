from __future__ import annotations

import json
from typing import Dict, List, Optional

from src.domain.repositories.interfaces import IMetricsRepository


class MetricsService:

    def __init__(self, metrics_repo: IMetricsRepository) -> None:
        self.metrics_repo = metrics_repo

    async def log_performance(
        self, name: str, duration_ms: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record api performance timing."""
        labels_str = json.dumps(labels) if labels else None
        await self.metrics_repo.add(
            metric_type="performance",
            name=name,
            value=duration_ms,
            labels=labels_str,
        )

    async def log_error(
        self, name: str, message: str, traceback: Optional[str] = None
    ) -> None:
        """Record occurrences of system exceptions."""
        labels = {"message": message}
        if traceback:
            labels["traceback"] = traceback

        await self.metrics_repo.add(
            metric_type="error",
            name=name,
            value=1.0,
            labels=json.dumps(labels),
        )

    async def get_metrics(self) -> List[dict]:
        """Fetch all gathered metrics."""
        return await self.metrics_repo.get_all()

    async def clear_metrics(self) -> None:
        """Clear all metrics logs."""
        await self.metrics_repo.clear()
