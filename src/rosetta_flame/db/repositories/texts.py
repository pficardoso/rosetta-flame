"""Texts submitted by the learner."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from rosetta_flame.db.repositories._common import dt_from_db, dt_to_db, new_id, require
from rosetta_flame.models.entities import Text

_SELECT = "SELECT id, content, submitted_at FROM text"


def _from_row(row: sqlite3.Row) -> Text:
    return Text(
        id=row["id"], content=row["content"], submitted_at=dt_from_db(row["submitted_at"])
    )


def create(conn: sqlite3.Connection, *, content: str, submitted_at: datetime) -> Text:
    text_id = new_id()
    conn.execute(
        "INSERT INTO text (id, content, submitted_at) VALUES (?, ?, ?)",
        (text_id, content, dt_to_db(submitted_at)),
    )
    return require(get(conn, text_id), "text")


def get(conn: sqlite3.Connection, text_id: str) -> Text | None:
    row = conn.execute(f"{_SELECT} WHERE id = ?", (text_id,)).fetchone()
    return _from_row(row) if row else None


def list_all(conn: sqlite3.Connection) -> list[Text]:
    """All texts, newest first."""
    rows = conn.execute(f"{_SELECT} ORDER BY submitted_at DESC, id DESC").fetchall()
    return [_from_row(row) for row in rows]
