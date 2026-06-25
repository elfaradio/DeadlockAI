from __future__ import annotations

from src.infrastructure.config import settings
from src.infrastructure.database.session import SessionLocal
from src.infrastructure.database.repositories import (
    ProcessRepository,
    ResourceRepository,
    EdgeRepository,
    SimulationEventRepository,
    AICacheRepository,
    MetricsRepository,
)
from src.application.services.simulation import SimulationService
from src.application.services.bankers import BankersService
from src.application.services.ai_explainer import AIExplainerService
from src.application.services.report import ReportService
from src.application.services.metrics import MetricsService


class Container:
    """Dependency Injection Container for the DeadlockAI application."""

    def __init__(self) -> None:
        self.settings = settings
        self.session_maker = SessionLocal

        # Repositories
        self.process_repo = ProcessRepository(self.session_maker)
        self.resource_repo = ResourceRepository(self.session_maker)
        self.edge_repo = EdgeRepository(self.session_maker)
        self.event_repo = SimulationEventRepository(self.session_maker)
        self.cache_repo = AICacheRepository(self.session_maker)
        self.metrics_repo = MetricsRepository(self.session_maker)

        # Services
        self.simulation_service = SimulationService(
            process_repo=self.process_repo,
            resource_repo=self.resource_repo,
            edge_repo=self.edge_repo,
            event_repo=self.event_repo,
        )
        self.bankers_service = BankersService()
        self.ai_explainer_service = AIExplainerService(
            cache_repo=self.cache_repo,
            metrics_repo=self.metrics_repo,
        )
        self.report_service = ReportService()
        self.metrics_service = MetricsService(metrics_repo=self.metrics_repo)


# Global dependency injection container instance
container = Container()


# Dependency injection resolver helpers for FastAPI Depends
def get_container() -> Container:
    return container


def get_simulation_service() -> SimulationService:
    return container.simulation_service


def get_bankers_service() -> BankersService:
    return container.bankers_service


def get_ai_explainer_service() -> AIExplainerService:
    return container.ai_explainer_service


def get_report_service() -> ReportService:
    return container.report_service


def get_metrics_service() -> MetricsService:
    return container.metrics_service
