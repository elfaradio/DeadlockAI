from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.presentation.api.main import app
from src.infrastructure.di.container import container

# Initialize TestClient
client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "DeadlockAI" in response.json()["service"]


def test_simulation_workflow_via_api() -> None:
    # 1. State empty
    response = client.get("/api/simulation/state")
    assert response.status_code == 200
    assert len(response.json()["processes"]) == 0

    # 2. Add Process P1
    response = client.post("/api/simulation/process", json={"pid": "P1", "state": "Waiting"})
    assert response.status_code == 201

    # 3. Modify Process P1 State
    response = client.put("/api/simulation/process/P1/state", json={"state": "Running"})
    assert response.status_code == 200

    # 4. Add Resource R1
    response = client.post("/api/simulation/resource", json={"rid": "R1", "total_instances": 2})
    assert response.status_code == 201

    # 5. Modify Resource R1 Instances
    response = client.put("/api/simulation/resource/R1", json={"total_instances": 4})
    assert response.status_code == 200

    # 6. Request Resource R1 by P1
    response = client.post("/api/simulation/request", json={"pid": "P1", "rid": "R1"})
    assert response.status_code == 200

    # 7. Allocate R1 to P1
    response = client.post("/api/simulation/allocate", json={"rid": "R1", "pid": "P1"})
    assert response.status_code == 200

    # 8. Release one instance of R1
    response = client.post("/api/simulation/resource/release-one?rid=R1")
    assert response.status_code == 200

    # 9. Release R1 from P1
    response = client.post("/api/simulation/release", json={"rid": "R1", "pid": "P1"})
    assert response.status_code == 200

    # 10. Delete Resource R1
    response = client.delete("/api/simulation/resource/R1")
    assert response.status_code == 200

    # 11. Delete Process P1
    response = client.delete("/api/simulation/process/P1")
    assert response.status_code == 200

    # 12. Reset
    response = client.post("/api/simulation/reset")
    assert response.status_code == 200


def test_validation_errors() -> None:
    # Attempt to create a process with an invalid ID structure (contains symbols)
    response = client.post("/api/simulation/process", json={"pid": "P@ss", "state": "Waiting"})
    assert response.status_code == 422  # Unprocessable Entity (Pydantic validation error)


def test_bankers_evaluate_via_api() -> None:
    payload = {
        "allocation": [[1, 0], [0, 1]],
        "maximum": [[1, 1], [1, 1]],
        "available": [1, 0],
        "process_names": ["P1", "P2"],
    }
    response = client.post("/api/bankers/evaluate", json=payload)
    assert response.status_code == 200
    assert response.json()["safe"] is True
    assert "P1" in response.json()["safe_sequence"]


def test_ai_explain_fallback_via_api() -> None:
    payload = {
        "deadlock_cycle": ["P1", "R1", "P2", "R2", "P1"],
        "processes": ["P1", "P2"],
        "resources": ["R1", "R2"],
        "banker_summary": "System is unsafe.",
    }
    response = client.get("/api/simulation/state") # populate metrics to avoid error
    response = client.post("/api/ai/explain", json=payload)
    assert response.status_code == 200
    assert "why_occurred" in response.json()


def test_ai_report_api() -> None:
    payload = {
        "processes": [{"pid": "P1", "state": "Running"}],
        "resources": [{"rid": "R1", "total_instances": 1, "allocated_instances": 1}],
        "allocations": [{"resource": "R1", "process": "P1"}],
        "deadlock_cycle": [],
        "ai_explanation": {
            "why_occurred": "Explanation",
            "coffman_conditions": [],
            "processes_involved": [],
            "resources_blocking": [],
            "resolution_strategies": [],
            "prevention_techniques": [],
            "banker_recommendation": "",
        },
    }
    response = client.post("/api/ai/report", json=payload)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 0


def test_metrics_api() -> None:
    client.get("/api/simulation/state")

    # Get metrics
    response = client.get("/api/metrics")
    assert response.status_code == 200
    assert len(response.json()) > 0

    # Clear metrics
    response = client.post("/api/metrics/clear")
    assert response.status_code == 200

    # Confirm cleared (could contain 1 metric representing the GET call latency itself)
    response = client.get("/api/metrics")
    assert len(response.json()) <= 1

    # Get tail logs
    response = client.get("/api/metrics/logs")
    assert response.status_code == 200
