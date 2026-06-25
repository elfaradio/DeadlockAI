from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
PROCESSES_FILE = DATA_DIR / "processes.json"
RESOURCES_FILE = DATA_DIR / "resources.json"
ALLOCATIONS_FILE = DATA_DIR / "allocations.json"

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.5-flash"


def load_json(path: Path, default: Any) -> Any:
	"""Load JSON from disk with safe fallback."""
	if not path.exists():
		return default
	with path.open("r", encoding="utf-8") as f:
		return json.load(f)


def save_json(path: Path, payload: Any) -> None:
	"""Persist JSON data to disk."""
	path.parent.mkdir(parents=True, exist_ok=True)
	with path.open("w", encoding="utf-8") as f:
		json.dump(payload, f, indent=2)