"""Exercises generated for a learning item."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Sequence
from datetime import datetime

from rosetta_flame.db.repositories._common import dt_from_db, dt_to_db, new_id, require
from rosetta_flame.models.entities import Exercise
from rosetta_flame.models.enums import ExerciseSource, ExerciseType

_SELECT = (
    "SELECT id, learning_item_id, type, prompt, answer, options_json, mistake_id, source,"
    " created_at FROM exercise"
)


def _from_row(row: sqlite3.Row) -> Exercise:
    options_json = row["options_json"]
    return Exercise(
        id=row["id"],
        learning_item_id=row["learning_item_id"],
        type=ExerciseType(row["type"]),
        prompt=row["prompt"],
        answer=row["answer"],
        source=ExerciseSource(row["source"]),
        created_at=dt_from_db(row["created_at"]),
        options=tuple(json.loads(options_json)) if options_json is not None else None,
        mistake_id=row["mistake_id"],
    )


def create(
    conn: sqlite3.Connection,
    *,
    learning_item_id: str,
    type: ExerciseType | str,
    prompt: str,
    answer: str,
    source: ExerciseSource | str,
    created_at: datetime,
    options: Sequence[str] | None = None,
    mistake_id: str | None = None,
) -> Exercise:
    exercise_id = new_id()
    conn.execute(
        "INSERT INTO exercise (id, learning_item_id, type, prompt, answer, options_json,"
        " mistake_id, source, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            exercise_id,
            learning_item_id,
            ExerciseType(type).value,
            prompt,
            answer,
            json.dumps(list(options)) if options is not None else None,
            mistake_id,
            ExerciseSource(source).value,
            dt_to_db(created_at),
        ),
    )
    return require(get(conn, exercise_id), "exercise")


def get(conn: sqlite3.Connection, exercise_id: str) -> Exercise | None:
    row = conn.execute(f"{_SELECT} WHERE id = ?", (exercise_id,)).fetchone()
    return _from_row(row) if row else None


def list_for_item(conn: sqlite3.Connection, learning_item_id: str) -> list[Exercise]:
    rows = conn.execute(
        f"{_SELECT} WHERE learning_item_id = ? ORDER BY created_at, id", (learning_item_id,)
    ).fetchall()
    return [_from_row(row) for row in rows]


def list_for_mistake(conn: sqlite3.Connection, mistake_id: str) -> list[Exercise]:
    rows = conn.execute(
        f"{_SELECT} WHERE mistake_id = ? ORDER BY created_at, id", (mistake_id,)
    ).fetchall()
    return [_from_row(row) for row in rows]
