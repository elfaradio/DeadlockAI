from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Optional
from src.domain.models.process import Process
from src.domain.models.resource import Resource
from src.domain.models.edge import Edge


class IProcessRepository(ABC):

    @abstractmethod
    async def get(self, pid: str) -> Optional[Process]:  # pragma: no cover
        pass

    @abstractmethod
    async def get_all(self) -> List[Process]:  # pragma: no cover
        pass

    @abstractmethod
    async def save(self, process: Process) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def delete(self, pid: str) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def clear(self) -> None:  # pragma: no cover
        pass


class IResourceRepository(ABC):

    @abstractmethod
    async def get(self, rid: str) -> Optional[Resource]:  # pragma: no cover
        pass

    @abstractmethod
    async def get_all(self) -> List[Resource]:  # pragma: no cover
        pass

    @abstractmethod
    async def save(self, resource: Resource) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def delete(self, rid: str) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def clear(self) -> None:  # pragma: no cover
        pass


class IEdgeRepository(ABC):

    @abstractmethod
    async def get_all(self) -> List[Edge]:  # pragma: no cover
        pass

    @abstractmethod
    async def add(self, edge: Edge) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def remove(self, from_node: str, to_node: str) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def delete_by_node(self, node: str) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def clear(self) -> None:  # pragma: no cover
        pass


class ISimulationEventRepository(ABC):

    @abstractmethod
    async def add(self, action: str, detail: str) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def get_all(self) -> List[dict]:  # pragma: no cover
        pass

    @abstractmethod
    async def clear(self) -> None:  # pragma: no cover
        pass


class IAICacheRepository(ABC):

    @abstractmethod
    async def get(self, prompt_hash: str) -> Optional[dict]:  # pragma: no cover
        pass

    @abstractmethod
    async def save(
        self,
        prompt_hash: str,
        prompt: str,
        response_json: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def clear(self) -> None:  # pragma: no cover
        pass


class IMetricsRepository(ABC):

    @abstractmethod
    async def add(
        self,
        metric_type: str,
        name: str,
        value: float,
        labels: Optional[str] = None,
    ) -> None:  # pragma: no cover
        pass

    @abstractmethod
    async def get_all(self) -> List[dict]:  # pragma: no cover
        pass

    @abstractmethod
    async def clear(self) -> None:  # pragma: no cover
        pass
