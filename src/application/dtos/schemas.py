from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field

from src.domain.models.edge import EdgeType
from src.domain.models.process import ProcessState

ID_PATTERN = r"^[a-zA-Z0-9_-]+$"


class ProcessCreateDTO(BaseModel):
    pid: str = Field(..., min_length=1, max_length=50, pattern=ID_PATTERN)
    state: ProcessState = ProcessState.WAITING


class ProcessUpdateStateDTO(BaseModel):
    state: ProcessState


class ResourceCreateDTO(BaseModel):
    rid: str = Field(..., min_length=1, max_length=50, pattern=ID_PATTERN)
    total_instances: int = Field(..., ge=1)


class ResourceUpdateDTO(BaseModel):
    total_instances: int = Field(..., ge=1)


class AllocateDTO(BaseModel):
    rid: str = Field(..., pattern=ID_PATTERN)
    pid: str = Field(..., pattern=ID_PATTERN)


class RequestDTO(BaseModel):
    pid: str = Field(..., pattern=ID_PATTERN)
    rid: str = Field(..., pattern=ID_PATTERN)


class ReleaseDTO(BaseModel):
    rid: str = Field(..., pattern=ID_PATTERN)
    pid: str = Field(..., pattern=ID_PATTERN)


class BankerEvaluateDTO(BaseModel):
    allocation: List[List[int]]
    maximum: List[List[int]]
    available: List[int]
    process_names: List[str]


class AIExplainRequestDTO(BaseModel):
    deadlock_cycle: List[str]
    processes: List[str]
    resources: List[str]
    banker_summary: Optional[str] = None
