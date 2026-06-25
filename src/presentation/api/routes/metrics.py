from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status

from src.application.services.metrics import MetricsService
from src.infrastructure.di.container import get_metrics_service

router = APIRouter(prefix="/api/metrics", tags=["Monitoring & Metrics"])


@router.get("")
async def get_metrics(service: MetricsService = Depends(get_metrics_service)):
    """Retrieve all logged system metrics."""
    return await service.get_metrics()


@router.post("/clear")
async def clear_metrics(service: MetricsService = Depends(get_metrics_service)):
    """Clear the metrics store."""
    await service.clear_metrics()
    return {"status": "success", "message": "Metrics store cleared"}


@router.get("/logs")
async def get_logs(lines: int = 100):
    """Retrieve the tail of application runtime logs."""
    log_file = Path("logs/app.log")
    if not log_file.exists():
        return {"logs": "No log file has been written yet."}

    try:
        with log_file.open("r", encoding="utf-8") as f:
            all_lines = f.readlines()
            tail = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return {"logs": "".join(tail)}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read application logs: {e}",
        )
