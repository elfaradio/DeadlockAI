from __future__ import annotations

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.presentation.api.main import migrate_json_to_sqlite
from src.infrastructure.di.container import container


@pytest.mark.asyncio
async def test_migrate_json_to_sqlite_workflow() -> None:
    # Set up folders
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)

    proc_file = data_dir / "processes.json"
    res_file = data_dir / "resources.json"
    alloc_file = data_dir / "allocations.json"

    # Mock legacy JSON data
    mock_processes = [{"pid": "P99", "state": "Waiting"}]
    mock_resources = [{"rid": "R99", "total_instances": 5, "allocated_instances": 1}]
    mock_allocations = [{"resource": "R99", "process": "P99"}]

    with proc_file.open("w", encoding="utf-8") as f:
        json.dump(mock_processes, f)
    with res_file.open("w", encoding="utf-8") as f:
        json.dump(mock_resources, f)
    with alloc_file.open("w", encoding="utf-8") as f:
        json.dump(mock_allocations, f)

    try:
        # Run migration on clean test DB
        await migrate_json_to_sqlite()

        # Check repository state
        p = await container.process_repo.get("P99")
        assert p is not None
        assert p.state.value == "Waiting"

        r = await container.resource_repo.get("R99")
        assert r is not None
        assert r.total_instances == 5
        assert r.allocated_instances == 1

        edges = await container.edge_repo.get_all()
        assert len(edges) > 0
        assert any(e.from_node == "R99" and e.to_node == "P99" for e in edges)

    finally:
        # Cleanup files
        for f_path in [proc_file, res_file, alloc_file]:
            if f_path.exists():
                try:
                    f_path.unlink()
                except OSError:
                    pass


@pytest.mark.asyncio
async def test_migrate_json_to_sqlite_empty_files() -> None:
    # Ensure it handles case when files don't exist
    data_dir = Path("data")
    proc_file = data_dir / "processes.json"
    if proc_file.exists():
        proc_file.unlink()

    # Clear repositories first
    await container.process_repo.clear()
    
    await migrate_json_to_sqlite()
    
    procs = await container.process_repo.get_all()
    assert len(procs) == 0


@pytest.mark.asyncio
async def test_migrate_json_to_sqlite_error_handling() -> None:
    # Test file reading crash handles exceptions gracefully without raising
    data_dir = Path("data")
    proc_file = data_dir / "processes.json"
    
    # Write invalid json syntax to trigger parse error
    with proc_file.open("w", encoding="utf-8") as f:
        f.write("{invalid_json:")

    try:
        # Should not raise exception
        await migrate_json_to_sqlite()
    finally:
        if proc_file.exists():
            proc_file.unlink()
            
    procs = await container.process_repo.get_all()
    assert len(procs) == 0
