from __future__ import annotations

import logging
import traceback
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from src.infrastructure.di.container import container

logger = logging.getLogger("deadlock_app")


class ExceptionHandlingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)
        except Exception as exc:
            err_msg = str(exc)
            tb = traceback.format_exc()
            logger.error(f"Unhandled exception during request processing: {err_msg}\n{tb}")

            try:
                await container.metrics_service.log_error(
                    name="api_unhandled_exception",
                    message=err_msg,
                    traceback=tb,
                )
            except Exception as e:
                logger.error(f"Failed to log error to database: {e}")

            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal Server Error",
                    "message": err_msg,
                },
            )
