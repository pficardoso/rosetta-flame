"""Mistakes found in the learner's texts."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Any

from rosetta_flame.db.repositories._common import (
    dt_from_db,
    dt_to_db,
    new_id,
    require,
    update_row,
)
from rosetta_flame.models.entities import Mistake

_UPDATABLE = frozenset({"weak_spot_id", "original", "correction", "explanation", "dismissed"})
_SELECT = (
    "SELECT id, text_id, weak_spot_id, original, correction, explanation, dismissed, created_at"
    " FROM mistake"
)


def _from_row(row: sqlite3.Row) -> Mistake:
    return Mistake(
        id=row["id"],
        text_id=row["text_id"],
        weak_spot_id=row["weak_spot_id"],
        original=row["original"],
        correction=row["correction"],
        explanation=row["explanation"],
        dismissed=bool(row["dismissed"]),
        created_at=dt_from_db(row["created_at"]),
    )


def create(
    conn: sqlite3.Connection,
    *,
    text_id: str,
    weak_spot_id: str,
    original: str,
    correction: str,
    created_at: datetime,
    explanation: str = "",
) -> Mistake:
    mistake_id = new_id()
    conn.execute(
        "INSERT INTO mistake (id, text_id, weak_spot_id, original, correction, explanation,"
        " created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            mistake_id,
            text_id,
            weak_spot_id,
            original,
            correction,
            explanation,
            dt_to_db(created_at),
        ),
    )
    return require(get(conn, mistake_id), "mistake")


def get(conn: sqlite3.Connection, mistake_id: str) -> Mistake | None:
    row = conn.execute(f"{_SELECT} WHERE id = ?", (mistake_id,)).fetchone()
    return _from_row(row) if row else None


def list_for_text(conn: sqlite3.Connection, text_id: str) -> list[Mistake]:
    rows = conn.execute(
        f"{_SELECT} WHERE text_id = ? ORDER BY created_at, id", (text_id,)
    ).fetchall()
    return [_from_row(row) for row in rows]


def list_for_weak_spot(
    conn: sqlite3.Connection, weak_spot_id: str, *, include_dismissed: bool = False
) -> list[Mistake]:
    sql = f"{_SELECT} WHERE weak_spot_id = ?"
    if not include_dismissed:
        sql += " AND dismissed = 0"
    rows = conn.execute(f"{sql} ORDER BY created_at, id", (weak_spot_id,)).fetchall()
    return [_from_row(row) for row in rows]


def update(conn: sqlite3.Connection, mistake_id: str, **fields: Any) -> Mistake:
    update_row(conn, "mistake", "id", mistake_id, fields, _UPDATABLE)
    return require(get(conn, mistake_id), "mistake")


def dismiss(conn: sqlite3.Connection, mistake_id: str, dismissed: bool = True) -> Mistake:
    return update(conn, mistake_id, dismissed=dismissed)
