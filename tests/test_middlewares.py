from __future__ import annotations

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import logging

from src.presentation.api.middleware.correlation import CorrelationIdMiddleware, correlation_id_ctx_var
from src.presentation.api.middleware.exception import ExceptionHandlingMiddleware
from src.presentation.api.middleware.metrics import RequestTimingMiddleware
from src.infrastructure.di.container import container


def create_test_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(ExceptionHandlingMiddleware)
    app.add_middleware(CorrelationIdMiddleware)
    app.add_middleware(RequestTimingMiddleware)

    @app.get("/ok")
    def ok_route():
        logger = logging.getLogger("deadlock_app")
        logger.info("Executing ok_route")
        # Check that context var is populated
        assert correlation_id_ctx_var.get() != ""
        return {"status": "ok"}

    @app.get("/raise-http")
    def raise_http():
        raise HTTPException(status_code=400, detail="Client Error")

    @app.get("/raise-unhandled")
    def raise_unhandled():
        raise ValueError("Unhandled Database Issue")

    return app


def test_correlation_id_generated_and_returned() -> None:
    app = create_test_app()
    client = TestClient(app)

    response = client.get("/ok")
    assert response.status_code == 200
    # Response must contain the custom header
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] != ""


def test_correlation_id_propagated() -> None:
    app = create_test_app()
    client = TestClient(app)

    custom_id = "test-uuid-correlation-123"
    response = client.get("/ok", headers={"X-Correlation-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["X-Correlation-ID"] == custom_id


def test_exception_handling_http_exception() -> None:
    app = create_test_app()
    client = TestClient(app)

    response = client.get("/raise-http")
    # Exception handling middleware catches unhandled exceptions; standard HTTPException is allowed to bubble
    # normally to FastAPI default handlers unless it's a raw generic Exception.
    assert response.status_code == 400
    assert response.json()["detail"] == "Client Error"


def test_exception_handling_unhandled_exception() -> None:
    app = create_test_app()
    client = TestClient(app)

    # Clean DB repository for test errors logs
    import asyncio
    asyncio.run(container.metrics_repo.clear())

    response = client.get("/raise-unhandled")
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal Server Error"
    assert "Unhandled Database Issue" in response.json()["message"]

    # Verify that error metric was written to DB
    metrics = asyncio.run(container.metrics_repo.get_all())
    assert len(metrics) > 0
    assert any(m["name"] == "api_unhandled_exception" for m in metrics)
