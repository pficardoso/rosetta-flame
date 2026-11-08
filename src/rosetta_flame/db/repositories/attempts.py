"""Attempts: the learner's answers to exercises."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime

from rosetta_flame.config import TIMEZONE
from rosetta_flame.db.repositories._common import (
    date_from_db,
    date_to_db,
    dt_from_db,
    dt_to_db,
    new_id,
    require,
)
from rosetta_flame.models.entities import Attempt
from rosetta_flame.utils.time import local_date

_SELECT = "SELECT a.id, a.exercise_id, a.correct, a.answered_at, a.local_date FROM attempt a"


def _from_row(row: sqlite3.Row) -> Attempt:
    return Attempt(
        id=row["id"],
        exercise_id=row["exercise_id"],
        correct=bool(row["correct"]),
        answered_at=dt_from_db(row["answered_at"]),
        local_date=date_from_db(row["local_date"]),
    )


def record(
    conn: sqlite3.Connection,
    *,
    exercise_id: str,
    correct: bool,
    answered_at: datetime,
    tz: str = TIMEZONE,
) -> Attempt:
    """Store an answer with its UTC time and the calendar day in the learner's timezone."""
    day = local_date(answered_at, tz)
    attempt_id = new_id()
    conn.execute(
        "INSERT INTO attempt (id, exercise_id, correct, answered_at, local_date)"
        " VALUES (?, ?, ?, ?, ?)",
        (attempt_id, exercise_id, int(correct), dt_to_db(answered_at), date_to_db(day)),
    )
    return require(get(conn, attempt_id), "attempt")


def get(conn: sqlite3.Connection, attempt_id: str) -> Attempt | None:
    row = conn.execute(f"{_SELECT} WHERE a.id = ?", (attempt_id,)).fetchone()
    return _from_row(row) if row else None


def list_for_exercise(conn: sqlite3.Connection, exercise_id: str) -> list[Attempt]:
    rows = conn.execute(
        f"{_SELECT} WHERE a.exercise_id = ? ORDER BY a.answered_at, a.id", (exercise_id,)
    ).fetchall()
    return [_from_row(row) for row in rows]


def list_for_item(conn: sqlite3.Connection, learning_item_id: str) -> list[Attempt]:
    """Every attempt on any exercise of the item, oldest first (the item's history)."""
    rows = conn.execute(
        f"{_SELECT} JOIN exercise e ON e.id = a.exercise_id"
        " WHERE e.learning_item_id = ? ORDER BY a.answered_at, a.id",
        (learning_item_id,),
    ).fetchall()
    return [_from_row(row) for row in rows]


def correct_days(conn: sqlite3.Connection, learning_item_id: str) -> list[date]:
    """Distinct calendar days on which the item had at least one correct answer."""
    rows = conn.execute(
        "SELECT DISTINCT a.local_date FROM attempt a JOIN exercise e ON e.id = a.exercise_id"
        " WHERE e.learning_item_id = ? AND a.correct = 1 ORDER BY a.local_date",
        (learning_item_id,),
    ).fetchall()
    return [date_from_db(row["local_date"]) for row in rows]
