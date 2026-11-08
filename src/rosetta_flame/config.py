"""Settings and constants."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_ROOT / "data"))
DB_PATH = Path(os.environ.get("ROSETTA_FLAME_DB", DATA_DIR / "rosetta_flame.db"))

# Calendar days (for example "5 different days" of practice) follow this timezone.
TIMEZONE = "Europe/Lisbon"
