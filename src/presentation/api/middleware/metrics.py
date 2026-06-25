from __future__ import annotations

import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.di.container import container

logger = logging.getLogger("deadlock_app")


class RequestTimingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000.0

        path = request.url.path
        # Skip logger for static doc urls to avoid inflating storage
        if not any(
            path.startswith(prefix)
            for prefix in ["/docs", "/openapi.json", "/redoc", "/favicon.ico"]
        ):
            try:
                await container.metrics_service.log_performance(
                    name="api_request_latency_ms",
                    duration_ms=duration_ms,
                    labels={
                        "path": path,
                        "method": request.method,
                        "status_code": str(response.status_code),
                    },
                )
            except Exception as e:
                logger.error(f"Failed to save request timing metric: {e}")

        return response
