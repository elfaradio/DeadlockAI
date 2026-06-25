from __future__ import annotations

import os
import pytest
from pathlib import Path

# Use a separate test database file for all test suites
TEST_DB_FILE = "./test_deadlock.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"

from src.infrastructure.database.session import init_db
from src.infrastructure.di.container import container
from src.infrastructure.database.models import (
    ProcessModel,
    ResourceModel,
    EdgeModel,
    SimulationEventModel,
    MetricModel,
    AICacheModel,
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Remove any old test DB file
    db_path = Path(TEST_DB_FILE)
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass

    # Initialize test database schema
    init_db()
    yield

    # Cleanup test DB file
    if db_path.exists():
        try:
            db_path.unlink()
        except OSError:
            pass


@pytest.fixture(autouse=True)
def clear_db_tables():
    # Clear all tables synchronously using SQLAlchemy session directly to support both sync/async tests
    with container.session_maker() as session:
        session.query(ProcessModel).delete()
        session.query(ResourceModel).delete()
        session.query(EdgeModel).delete()
        session.query(SimulationEventModel).delete()
        session.query(MetricModel).delete()
        session.query(AICacheModel).delete()
        session.commit()
