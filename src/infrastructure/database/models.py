from __future__ import annotations

from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from src.infrastructure.database.session import Base


class ProcessModel(Base):
    __tablename__ = "processes"
    pid = Column(String, primary_key=True, index=True)
    state = Column(String, nullable=False, default="Waiting")


class ResourceModel(Base):
    __tablename__ = "resources"
    rid = Column(String, primary_key=True, index=True)
    total_instances = Column(Integer, nullable=False, default=1)
    allocated_instances = Column(Integer, nullable=False, default=0)


class EdgeModel(Base):
    __tablename__ = "edges"
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_node = Column(String, nullable=False, index=True)
    to_node = Column(String, nullable=False, index=True)
    edge_type = Column(String, nullable=False)  # 'request' or 'allocation'


class SimulationEventModel(Base):
    __tablename__ = "simulation_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    action = Column(String, nullable=False)
    detail = Column(Text, nullable=False)


class AICacheModel(Base):
    __tablename__ = "ai_cache"
    prompt_hash = Column(String, primary_key=True, index=True)
    prompt = Column(Text, nullable=False)
    response_json = Column(Text, nullable=False)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class MetricModel(Base):
    __tablename__ = "metrics"
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    metric_type = Column(String, nullable=False, index=True)  # 'latency', 'error', 'token_count'
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    labels = Column(Text, nullable=True)  # JSON metadata string
