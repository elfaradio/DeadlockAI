from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.domain.models.process import ProcessState
from src.infrastructure.database.models import Base
from src.infrastructure.database.repositories import (
    ProcessRepository,
    ResourceRepository,
    EdgeRepository,
    SimulationEventRepository,
)
from src.application.services.simulation import SimulationService


@pytest.fixture
def in_memory_db():
    # Use StaticPool to persist in-memory SQLite connection across sessions
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_maker = sessionmaker(bind=engine)
    return session_maker


@pytest.fixture
def simulation_service(in_memory_db):
    proc_repo = ProcessRepository(in_memory_db)
    res_repo = ResourceRepository(in_memory_db)
    edge_repo = EdgeRepository(in_memory_db)
    event_repo = SimulationEventRepository(in_memory_db)

    return SimulationService(
        process_repo=proc_repo,
        resource_repo=res_repo,
        edge_repo=edge_repo,
        event_repo=event_repo,
    )


@pytest.mark.asyncio
async def test_create_and_delete_process(simulation_service) -> None:
    # Create Process
    await simulation_service.create_process("P1", ProcessState.WAITING)
    state = await simulation_service.get_state()
    assert len(state["processes"]) == 1
    assert state["processes"][0]["pid"] == "P1"
    assert state["processes"][0]["state"] == "Waiting"

    # Delete Process
    await simulation_service.delete_process("P1")
    state = await simulation_service.get_state()
    assert len(state["processes"]) == 0


@pytest.mark.asyncio
async def test_create_and_update_resource(simulation_service) -> None:
    # Create Resource
    await simulation_service.create_resource("R1", 3)
    state = await simulation_service.get_state()
    assert len(state["resources"]) == 1
    assert state["resources"][0]["rid"] == "R1"
    assert state["resources"][0]["total_instances"] == 3

    # Update instances
    await simulation_service.update_resource_instances("R1", 5)
    state = await simulation_service.get_state()
    assert state["resources"][0]["total_instances"] == 5


@pytest.mark.asyncio
async def test_allocate_and_request_workflow(simulation_service) -> None:
    # Create elements
    await simulation_service.create_process("P1", ProcessState.WAITING)
    await simulation_service.create_process("P2", ProcessState.WAITING)
    await simulation_service.create_resource("R1", 1)

    # Allocate R1 to P1
    await simulation_service.allocate("R1", "P1")
    state = await simulation_service.get_state()
    assert len(state["allocations"]) == 1
    assert state["allocations"][0] == {"resource": "R1", "process": "P1"}
    # P1 state should transition to Running
    assert state["processes"][0]["state"] == "Running"

    # Request R1 by P2 (which is already allocated)
    await simulation_service.request("P2", "R1")
    state = await simulation_service.get_state()
    assert len(state["requests"]) == 1
    assert state["requests"][0] == {"process": "P2", "resource": "R1"}

    # P2 state should transition to Blocked
    for p in state["processes"]:
        if p["pid"] == "P2":
            assert p["state"] == "Blocked"


@pytest.mark.asyncio
async def test_deadlock_detection_cycle(simulation_service) -> None:
    await simulation_service.create_process("P1", ProcessState.WAITING)
    await simulation_service.create_process("P2", ProcessState.WAITING)
    await simulation_service.create_resource("R1", 1)
    await simulation_service.create_resource("R2", 1)

    # Allocation edges: R1->P1, R2->P2
    await simulation_service.allocate("R1", "P1")
    await simulation_service.allocate("R2", "P2")

    # Request edges: P1->R2, P2->R1
    await simulation_service.request("P1", "R2")
    await simulation_service.request("P2", "R1")

    state = await simulation_service.get_state()
    assert state["deadlock"]["is_deadlocked"] is True
    assert "P1" in state["deadlock"]["processes"]
    assert "R1" in state["deadlock"]["resources"]
