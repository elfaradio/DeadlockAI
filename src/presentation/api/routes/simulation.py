from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from src.application.dtos.schemas import (
    ProcessCreateDTO,
    ProcessUpdateStateDTO,
    ResourceCreateDTO,
    ResourceUpdateDTO,
    AllocateDTO,
    RequestDTO,
    ReleaseDTO,
)
from src.application.services.simulation import SimulationService
from src.infrastructure.di.container import get_simulation_service

router = APIRouter(prefix="/api/simulation", tags=["Simulation"])


@router.get("/state", response_model=Dict[str, Any])
async def get_state(service: SimulationService = Depends(get_simulation_service)):
    return await service.get_state()


@router.post("/process", status_code=status.HTTP_201_CREATED)
async def create_process(
    dto: ProcessCreateDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        await service.create_process(dto.pid, dto.state)
        return {"status": "success", "message": f"Process {dto.pid} created"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/process/{pid}")
async def delete_process(
    pid: str,
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        await service.delete_process(pid)
        return {"status": "success", "message": f"Process {pid} deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/process/{pid}/state")
async def update_process_state(
    pid: str,
    dto: ProcessUpdateStateDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        await service.set_process_state(pid, dto.state)
        return {"status": "success", "message": f"Process {pid} state updated"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/resource", status_code=status.HTTP_201_CREATED)
async def create_resource(
    dto: ResourceCreateDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        await service.create_resource(dto.rid, dto.total_instances)
        return {"status": "success", "message": f"Resource {dto.rid} created"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/resource/{rid}")
async def delete_resource(
    rid: str,
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        await service.delete_resource(rid)
        return {"status": "success", "message": f"Resource {rid} deleted"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/resource/{rid}")
async def update_resource_instances(
    rid: str,
    dto: ResourceUpdateDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        await service.update_resource_instances(rid, dto.total_instances)
        return {"status": "success", "message": f"Resource {rid} instances updated"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/resource/release-one")
async def release_one_instance(
    rid: str,
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        await service.release_one_instance(rid)
        return {"status": "success", "message": f"Released one instance of resource {rid}"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/allocate")
async def allocate(
    dto: AllocateDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        await service.allocate(dto.rid, dto.pid)
        return {"status": "success", "message": f"Allocated {dto.rid} to {dto.pid}"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/request")
async def request_edge(
    dto: RequestDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        await service.request(dto.pid, dto.rid)
        return {"status": "success", "message": f"Request edge added: {dto.pid} -> {dto.rid}"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/release")
async def release(
    dto: ReleaseDTO,
    service: SimulationService = Depends(get_simulation_service),
):
    try:
        await service.release(dto.rid, dto.pid)
        return {"status": "success", "message": f"Released {dto.rid} from {dto.pid}"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/reset")
async def reset(service: SimulationService = Depends(get_simulation_service)):
    await service.reset()
    return {"status": "success", "message": "Simulation reset completed"}
