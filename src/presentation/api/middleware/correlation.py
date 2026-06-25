from __future__ import annotations

import contextvars
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context-local storage for request correlation IDs
correlation_id_ctx_var = contextvars.ContextVar("correlation_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next) -> Response:
        # Capture client-provided correlation ID or generate a new UUID
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        token = correlation_id_ctx_var.set(correlation_id)
        try:
            response = await call_next(request)
            response.headers["X-Correlation-ID"] = correlation_id
            return response
        finally:
            correlation_id_ctx_var.reset(token)
