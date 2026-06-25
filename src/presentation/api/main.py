from __future__ import annotations

from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.database.session import init_db
from src.presentation.api.middleware.correlation import CorrelationIdMiddleware
from src.presentation.api.middleware.exception import ExceptionHandlingMiddleware
from src.presentation.api.middleware.metrics import RequestTimingMiddleware
from src.presentation.api.routes import ai, bankers, metrics, simulation
from src.infrastructure.di.container import container


async def migrate_json_to_sqlite():
    """Migrate legacy JSON files to SQLite database on first startup if DB is empty."""
    import json
    import logging
    from pathlib import Path
    from src.domain.models.process import Process, ProcessState
    from src.domain.models.resource import Resource
    from src.domain.models.edge import Edge, EdgeType

    logger = logging.getLogger("deadlock_app")
    existing_procs = await container.process_repo.get_all()
    if existing_procs:
        return

    data_dir = Path("data")
    proc_file = data_dir / "processes.json"
    res_file = data_dir / "resources.json"
    alloc_file = data_dir / "allocations.json"

    if not proc_file.exists() and not res_file.exists():
        return

    logger.info("Migrating legacy JSON data to SQLite database...")
    try:
        # Load processes
        if proc_file.exists():
            with proc_file.open("r", encoding="utf-8") as f:
                procs_data = json.load(f)
                for p_dict in procs_data:
                    pid = p_dict["pid"]
                    state = ProcessState(p_dict.get("state", "Waiting"))
                    await container.process_repo.save(Process(pid=pid, state=state))

        # Load resources
        if res_file.exists():
            with res_file.open("r", encoding="utf-8") as f:
                res_data = json.load(f)
                for r_dict in res_data:
                    rid = r_dict["rid"]
                    total = r_dict["total_instances"]
                    allocated = r_dict.get("allocated_instances", 0)
                    await container.resource_repo.save(
                        Resource(
                            rid=rid,
                            total_instances=total,
                            allocated_instances=allocated,
                        )
                    )

        # Load allocations
        if alloc_file.exists():
            with alloc_file.open("r", encoding="utf-8") as f:
                alloc_data = json.load(f)
                for a_dict in alloc_data:
                    rid = a_dict["resource"]
                    pid = a_dict["process"]
                    await container.edge_repo.add(
                        Edge(
                            from_node=rid,
                            to_node=pid,
                            edge_type=EdgeType.ALLOCATION,
                        )
                    )
        logger.info("Migration from JSON to SQLite completed successfully!")
    except Exception as e:
        logger.error(f"Migration from JSON to SQLite failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern context manager for application startup and shutdown lifespan."""
    init_db()
    await migrate_json_to_sqlite()
    yield


app = FastAPI(
    title="DeadlockAI Enterprise API",
    description="Clean Architecture, High-Performance Backend API for Deadlock Detection, Banker's Safety, and AI Analysis.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handling middleware first to catch everything
app.add_middleware(ExceptionHandlingMiddleware)
# Add correlation ID request tracing
app.add_middleware(CorrelationIdMiddleware)
# Request latency tracking middleware
app.add_middleware(RequestTimingMiddleware)

# Register API endpoints
app.include_router(simulation.router)
app.include_router(bankers.router)
app.include_router(ai.router)
app.include_router(metrics.router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "DeadlockAI REST API",
        "status": "healthy",
        "documentation": "/docs",
    }


if __name__ == "__main__":
    from src.infrastructure.config import settings

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
    )
