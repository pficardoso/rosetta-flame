"""SQLite connection handling."""

from __future__ import annotations

import itertools
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

_savepoint_ids = itertools.count(1)


def connect(path: str | Path = ":memory:") -> sqlite3.Connection:
    """Open a database with foreign keys on and rows addressable by column name.

    The connection is in autocommit mode. Group related writes with :func:`transaction`.
    """
    target = str(path)
    if target != ":memory:":
        Path(target).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, isolation_level=None)
    # Set up the connection with desired settings 
    conn.row_factory = sqlite3.Row # Access rows by column name 
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a block atomically: it is committed on success and rolled back on error.

    Uses savepoints, so it nests safely inside another ``transaction``.
    """
    name = f"sp_{next(_savepoint_ids)}"
    conn.execute(f"SAVEPOINT {name}")
    try:
        yield conn
    except BaseException:
        conn.execute(f"ROLLBACK TO {name}")
        conn.execute(f"RELEASE {name}")
        raise
    else:
        conn.execute(f"RELEASE {name}")
