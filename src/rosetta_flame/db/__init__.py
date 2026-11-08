"""The data layer: SQLite connection, migrations and repositories."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from rosetta_flame.config import DB_PATH
from rosetta_flame.db.connection import connect, transaction
from rosetta_flame.db.migrate import apply_migrations


def open_database(path: str | Path | None = None) -> sqlite3.Connection:
    """Open the database (default: the configured file) and bring its schema up to date."""
    conn = connect(DB_PATH if path is None else path)
    apply_migrations(conn)
    return conn


__all__ = ["apply_migrations", "connect", "open_database", "transaction"]
