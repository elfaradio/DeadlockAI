from __future__ import annotations

import sys
from pathlib import Path
from src.presentation.web.dashboard import main

# Append the project root to sys.path so src imports function correctly
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    main()