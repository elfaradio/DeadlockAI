from __future__ import annotations

import networkx as nx
from typing import List, Dict, Any, Optional

from src.domain.models.process import Process, ProcessState
from src.domain.models.resource import Resource
from src.domain.models.edge import Edge, EdgeType
from src.domain.models.deadlock import DeadlockResult, detect_deadlock
from src.domain.repositories.interfaces import (
    IProcessRepository,
    IResourceRepository,
    IEdgeRepository,
    ISimulationEventRepository,
)


class SimulationService:

    def __init__(
        self,
        process_repo: IProcessRepository,
        resource_repo: IResourceRepository,
        edge_repo: IEdgeRepository,
        event_repo: ISimulationEventRepository,
    ) -> None:
        self.process_repo = process_repo
        self.resource_repo = resource_repo
        self.edge_repo = edge_repo
        self.event_repo = event_repo

    async def get_state(self) -> Dict[str, Any]:
        processes = await self.process_repo.get_all()
        resources = await self.resource_repo.get_all()
        edges = await self.edge_repo.get_all()
        events = await self.event_repo.get_all()

        graph = self._build_graph(processes, resources, edges)
        deadlock_res = detect_deadlock(graph)

        return {
            "processes": [
                {"pid": p.pid, "state": p.state.value} for p in processes
            ],
            "resources": [
                {
                    "rid": r.rid,
                    "total_instances": r.total_instances,
                    "allocated_instances": r.allocated_instances,
                    "available_instances": r.available_instances,
                }
                for r in resources
            ],
            "allocations": [
                {"resource": e.from_node, "process": e.to_node}
                for e in edges
                if e.edge_type == EdgeType.ALLOCATION
            ],
            "requests": [
                {"process": e.from_node, "resource": e.to_node}
                for e in edges
                if e.edge_type == EdgeType.REQUEST
            ],
            "deadlock": {
                "is_deadlocked": deadlock_res.is_deadlocked,
                "cycle": deadlock_res.cycle,
                "processes": deadlock_res.processes,
                "resources": deadlock_res.resources,
            },
            "timeline": events,
        }

    async def create_process(self, pid: str, state: ProcessState) -> None:
        existing = await self.process_repo.get(pid)
        if existing:
            raise ValueError(f"Process {pid} already exists")

        process = Process(pid=pid, state=state)
        await self.process_repo.save(process)
        await self.event_repo.add(
            "Create Process", f"{pid} created with state {state.value}"
        )

    async def delete_process(self, pid: str) -> None:
        existing = await self.process_repo.get(pid)
        if not existing:
            raise ValueError(f"Process {pid} does not exist")

        # Get edges related to this process
        edges = await self.edge_repo.get_all()
        for edge in edges:
            if edge.from_node == pid or edge.to_node == pid:
                # If it's an allocation edge, decrement allocated instances on the resource
                if edge.edge_type == EdgeType.ALLOCATION:
                    resource = await self.resource_repo.get(edge.from_node)
                    if resource:
                        resource.allocated_instances = max(
                            0, resource.allocated_instances - 1
                        )
                        await self.resource_repo.save(resource)

        await self.process_repo.delete(pid)
        await self.edge_repo.delete_by_node(pid)
        await self.event_repo.add("Delete Process", f"{pid} deleted")

    async def set_process_state(self, pid: str, state: ProcessState) -> None:
        process = await self.process_repo.get(pid)
        if not process:
            raise ValueError(f"Process {pid} does not exist")
        process.state = state
        await self.process_repo.save(process)
        await self.event_repo.add(
            "Update Process State", f"{pid} -> {state.value}"
        )

    async def create_resource(self, rid: str, total_instances: int) -> None:
        if total_instances < 1:
            raise ValueError("Instances must be >= 1")
        existing = await self.resource_repo.get(rid)
        if existing:
            raise ValueError(f"Resource {rid} already exists")

        resource = Resource(rid=rid, total_instances=total_instances)
        await self.resource_repo.save(resource)
        await self.event_repo.add(
            "Create Resource", f"{rid} created with {total_instances} instances"
        )

    async def delete_resource(self, rid: str) -> None:
        existing = await self.resource_repo.get(rid)
        if not existing:
            raise ValueError(f"Resource {rid} does not exist")

        await self.resource_repo.delete(rid)
        await self.edge_repo.delete_by_node(rid)
        await self.event_repo.add("Delete Resource", f"{rid} deleted")

    async def update_resource_instances(self, rid: str, instances: int) -> None:
        resource = await self.resource_repo.get(rid)
        if not resource:
            raise ValueError(f"Resource {rid} does not exist")
        if instances < resource.allocated_instances:
            raise ValueError("Instances cannot be less than allocated instances")
        resource.total_instances = instances
        await self.resource_repo.save(resource)
        await self.event_repo.add(
            "Update Resource", f"{rid} total instances -> {instances}"
        )

    async def release_one_instance(self, rid: str) -> None:
        resource = await self.resource_repo.get(rid)
        if not resource:
            raise ValueError(f"Resource {rid} does not exist")
        if resource.allocated_instances < 1:
            raise ValueError(f"No allocated instances to release for {rid}")

        resource.allocated_instances -= 1
        await self.resource_repo.save(resource)
        await self.event_repo.add(
            "Release Resource", f"1 instance released from {rid}"
        )

    async def allocate(self, rid: str, pid: str) -> None:
        resource = await self.resource_repo.get(rid)
        process = await self.process_repo.get(pid)
        if not resource:
            raise ValueError(f"Resource {rid} does not exist")
        if not process:
            raise ValueError(f"Process {pid} does not exist")

        if resource.available_instances < 1:
            raise ValueError(f"Not enough available instances for {rid}")

        # Check if process is requesting this resource. If so, remove the request edge.
        await self.edge_repo.remove(pid, rid)

        # Create allocation edge (rid -> pid)
        edge = Edge(from_node=rid, to_node=pid, edge_type=EdgeType.ALLOCATION)
        await self.edge_repo.add(edge)

        # Update resource allocation
        resource.allocated_instances += 1
        await self.resource_repo.save(resource)

        # Update process state to Running
        process.state = ProcessState.RUNNING
        await self.process_repo.save(process)

        await self.event_repo.add("Allocate", f"{rid} allocated to {pid}")

    async def request(self, pid: str, rid: str) -> None:
        resource = await self.resource_repo.get(rid)
        process = await self.process_repo.get(pid)
        if not resource:
            raise ValueError(f"Resource {rid} does not exist")
        if not process:
            raise ValueError(f"Process {pid} does not exist")

        # Create request edge (pid -> rid)
        edge = Edge(from_node=pid, to_node=rid, edge_type=EdgeType.REQUEST)
        await self.edge_repo.add(edge)

        # Update process state to Blocked
        process.state = ProcessState.BLOCKED
        await self.process_repo.save(process)

        await self.event_repo.add("Request", f"{pid} requested {rid}")

    async def release(self, rid: str, pid: str) -> None:
        resource = await self.resource_repo.get(rid)
        if not resource:
            raise ValueError(f"Resource {rid} does not exist")

        # Remove allocation edge (rid -> pid)
        await self.edge_repo.remove(rid, pid)

        # Update resource allocation
        resource.allocated_instances = max(0, resource.allocated_instances - 1)
        await self.resource_repo.save(resource)

        await self.event_repo.add("Release", f"{rid} released from {pid}")

    async def reset(self) -> None:
        await self.process_repo.clear()
        await self.resource_repo.clear()
        await self.edge_repo.clear()
        await self.event_repo.clear()
        await self.event_repo.add("Reset", "Simulation reset")

    def _build_graph(
        self,
        processes: List[Process],
        resources: List[Resource],
        edges: List[Edge],
    ) -> nx.DiGraph:
        graph = nx.DiGraph()
        for p in processes:
            graph.add_node(p.pid, kind="process")
        for r in resources:
            graph.add_node(r.rid, kind="resource")
        for e in edges:
            graph.add_edge(e.from_node, e.to_node, edge_type=e.edge_type.value)
        return graph
