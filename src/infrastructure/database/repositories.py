from __future__ import annotations

import asyncio
from datetime import datetime
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import sessionmaker

from src.domain.models.edge import Edge, EdgeType
from src.domain.models.process import Process, ProcessState
from src.domain.models.resource import Resource
from src.domain.repositories.interfaces import (
    IAICacheRepository,
    IEdgeRepository,
    IMetricsRepository,
    IProcessRepository,
    IResourceRepository,
    ISimulationEventRepository,
)
from src.infrastructure.database.models import (
    AICacheModel,
    EdgeModel,
    MetricModel,
    ProcessModel,
    ResourceModel,
    SimulationEventModel,
)


class ProcessRepository(IProcessRepository):

    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    async def get(self, pid: str) -> Optional[Process]:
        def _get():
            with self.session_maker() as session:
                model = session.query(ProcessModel).filter(ProcessModel.pid == pid).first()
                if not model:
                    return None
                return Process(pid=model.pid, state=ProcessState(model.state))
        return await asyncio.to_thread(_get)

    async def get_all(self) -> List[Process]:
        def _get_all():
            with self.session_maker() as session:
                models = session.query(ProcessModel).all()
                return [Process(pid=m.pid, state=ProcessState(m.state)) for m in models]
        return await asyncio.to_thread(_get_all)

    async def save(self, process: Process) -> None:
        def _save():
            with self.session_maker() as session:
                model = (
                    session.query(ProcessModel)
                    .filter(ProcessModel.pid == process.pid)
                    .first()
                )
                if model:
                    model.state = process.state.value
                else:
                    model = ProcessModel(pid=process.pid, state=process.state.value)
                    session.add(model)
                session.commit()
        return await asyncio.to_thread(_save)

    async def delete(self, pid: str) -> None:
        def _delete():
            with self.session_maker() as session:
                session.query(ProcessModel).filter(ProcessModel.pid == pid).delete()
                session.commit()
        return await asyncio.to_thread(_delete)

    async def clear(self) -> None:
        def _clear():
            with self.session_maker() as session:
                session.query(ProcessModel).delete()
                session.commit()
        return await asyncio.to_thread(_clear)


class ResourceRepository(IResourceRepository):

    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    async def get(self, rid: str) -> Optional[Resource]:
        def _get():
            with self.session_maker() as session:
                model = session.query(ResourceModel).filter(ResourceModel.rid == rid).first()
                if not model:
                    return None
                return Resource(
                    rid=model.rid,
                    total_instances=model.total_instances,
                    allocated_instances=model.allocated_instances,
                )
        return await asyncio.to_thread(_get)

    async def get_all(self) -> List[Resource]:
        def _get_all():
            with self.session_maker() as session:
                models = session.query(ResourceModel).all()
                return [
                    Resource(
                        rid=m.rid,
                        total_instances=m.total_instances,
                        allocated_instances=m.allocated_instances,
                    )
                    for m in models
                ]
        return await asyncio.to_thread(_get_all)

    async def save(self, resource: Resource) -> None:
        def _save():
            with self.session_maker() as session:
                model = (
                    session.query(ResourceModel)
                    .filter(ResourceModel.rid == resource.rid)
                    .first()
                )
                if model:
                    model.total_instances = resource.total_instances
                    model.allocated_instances = resource.allocated_instances
                else:
                    model = ResourceModel(
                        rid=resource.rid,
                        total_instances=resource.total_instances,
                        allocated_instances=resource.allocated_instances,
                    )
                    session.add(model)
                session.commit()
        return await asyncio.to_thread(_save)

    async def delete(self, rid: str) -> None:
        def _delete():
            with self.session_maker() as session:
                session.query(ResourceModel).filter(ResourceModel.rid == rid).delete()
                session.commit()
        return await asyncio.to_thread(_delete)

    async def clear(self) -> None:
        def _clear():
            with self.session_maker() as session:
                session.query(ResourceModel).delete()
                session.commit()
        return await asyncio.to_thread(_clear)


class EdgeRepository(IEdgeRepository):

    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    async def get_all(self) -> List[Edge]:
        def _get_all():
            with self.session_maker() as session:
                models = session.query(EdgeModel).all()
                return [
                    Edge(
                        from_node=m.from_node,
                        to_node=m.to_node,
                        edge_type=EdgeType(m.edge_type),
                    )
                    for m in models
                ]
        return await asyncio.to_thread(_get_all)

    async def add(self, edge: Edge) -> None:
        def _add():
            with self.session_maker() as session:
                exists = (
                    session.query(EdgeModel)
                    .filter(
                        EdgeModel.from_node == edge.from_node,
                        EdgeModel.to_node == edge.to_node,
                        EdgeModel.edge_type == edge.edge_type.value,
                    )
                    .first()
                )
                if not exists:
                    model = EdgeModel(
                        from_node=edge.from_node,
                        to_node=edge.to_node,
                        edge_type=edge.edge_type.value,
                    )
                    session.add(model)
                    session.commit()
        return await asyncio.to_thread(_add)

    async def remove(self, from_node: str, to_node: str) -> None:
        def _remove():
            with self.session_maker() as session:
                session.query(EdgeModel).filter(
                    EdgeModel.from_node == from_node, EdgeModel.to_node == to_node
                ).delete()
                session.commit()
        return await asyncio.to_thread(_remove)

    async def delete_by_node(self, node: str) -> None:
        def _delete_by_node():
            with self.session_maker() as session:
                session.query(EdgeModel).filter(
                    or_(EdgeModel.from_node == node, EdgeModel.to_node == node)
                ).delete()
                session.commit()
        return await asyncio.to_thread(_delete_by_node)

    async def clear(self) -> None:
        def _clear():
            with self.session_maker() as session:
                session.query(EdgeModel).delete()
                session.commit()
        return await asyncio.to_thread(_clear)


class SimulationEventRepository(ISimulationEventRepository):

    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    async def add(self, action: str, detail: str) -> None:
        def _add():
            with self.session_maker() as session:
                model = SimulationEventModel(
                    action=action, detail=detail, timestamp=datetime.utcnow()
                )
                session.add(model)
                session.commit()
        return await asyncio.to_thread(_add)

    async def get_all(self) -> List[dict]:
        def _get_all():
            with self.session_maker() as session:
                models = (
                    session.query(SimulationEventModel)
                    .order_by(SimulationEventModel.timestamp.desc())
                    .all()
                )
                return [
                    {
                        "timestamp": m.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        "action": m.action,
                        "detail": m.detail,
                    }
                    for m in models
                ]
        return await asyncio.to_thread(_get_all)

    async def clear(self) -> None:
        def _clear():
            with self.session_maker() as session:
                session.query(SimulationEventModel).delete()
                session.commit()
        return await asyncio.to_thread(_clear)


class AICacheRepository(IAICacheRepository):

    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    async def get(self, prompt_hash: str) -> Optional[dict]:
        def _get():
            with self.session_maker() as session:
                model = (
                    session.query(AICacheModel)
                    .filter(AICacheModel.prompt_hash == prompt_hash)
                    .first()
                )
                if not model:
                    return None
                return {
                    "prompt_hash": model.prompt_hash,
                    "prompt": model.prompt,
                    "response_json": model.response_json,
                    "prompt_tokens": model.prompt_tokens,
                    "completion_tokens": model.completion_tokens,
                    "created_at": model.created_at,
                }
        return await asyncio.to_thread(_get)

    async def save(
        self,
        prompt_hash: str,
        prompt: str,
        response_json: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:
        def _save():
            with self.session_maker() as session:
                exists = (
                    session.query(AICacheModel)
                    .filter(AICacheModel.prompt_hash == prompt_hash)
                    .first()
                )
                if exists:
                    exists.response_json = response_json
                    exists.prompt_tokens = prompt_tokens
                    exists.completion_tokens = completion_tokens
                    exists.created_at = datetime.utcnow()
                else:
                    model = AICacheModel(
                        prompt_hash=prompt_hash,
                        prompt=prompt,
                        response_json=response_json,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens,
                        created_at=datetime.utcnow(),
                    )
                    session.add(model)
                session.commit()
        return await asyncio.to_thread(_save)

    async def clear(self) -> None:
        def _clear():
            with self.session_maker() as session:
                session.query(AICacheModel).delete()
                session.commit()
        return await asyncio.to_thread(_clear)


class MetricsRepository(IMetricsRepository):

    def __init__(self, session_maker: sessionmaker) -> None:
        self.session_maker = session_maker

    async def add(
        self,
        metric_type: str,
        name: str,
        value: float,
        labels: Optional[str] = None,
    ) -> None:
        def _add():
            with self.session_maker() as session:
                model = MetricModel(
                    metric_type=metric_type,
                    name=name,
                    value=value,
                    labels=labels,
                    timestamp=datetime.utcnow(),
                )
                session.add(model)
                session.commit()
        return await asyncio.to_thread(_add)

    async def get_all(self) -> List[dict]:
        def _get_all():
            with self.session_maker() as session:
                models = session.query(MetricModel).order_by(MetricModel.timestamp.desc()).all()
                return [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "metric_type": m.metric_type,
                        "name": m.name,
                        "value": m.value,
                        "labels": m.labels,
                    }
                    for m in models
                ]
        return await asyncio.to_thread(_get_all)

    async def clear(self) -> None:
        def _clear():
            with self.session_maker() as session:
                session.query(MetricModel).delete()
                session.commit()
        return await asyncio.to_thread(_clear)
