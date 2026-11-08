"""Topics: the items of the teaching program."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from typing import Any

from rosetta_flame.db.connection import transaction
from rosetta_flame.db.repositories._common import new_id, require, update_row
from rosetta_flame.models.entities import Topic
from rosetta_flame.models.enums import ItemType, Level, TopicType

_UPDATABLE = frozenset(
    {
        "code",
        "name",
        "description",
        "type",
        "category",
        "main_level",
        "also_levels",
        "unit",
        "order_in_program",
        "source_program",
        "source_ref",
    }
)
_COLUMNS = (
    "id, code, name, description, type, category, main_level, also_levels,"
    " unit, order_in_program, source_program, source_ref"
)
_SELECT = f"SELECT {_COLUMNS} FROM topic"
_SEPARATOR = ";"


def parse_levels(value: str | Iterable[Level | str] | None) -> tuple[Level, ...]:
    """Turn 'A2;B1', ['A2', 'B1'] or None into (Level.A2, Level.B1)."""
    if value is None:
        return ()
    parts = value.split(_SEPARATOR) if isinstance(value, str) else list(value)
    return tuple(Level(part.strip()) for part in parts if str(part).strip())


def levels_to_db(levels: tuple[Level, ...]) -> str:
    return _SEPARATOR.join(level.value for level in levels)


def check_levels(
    main_level: Level | str | None, also_levels: str | Iterable[Level | str] | None
) -> tuple[Level | None, tuple[Level, ...]]:
    """Validate the pair and return it normalised.

    Every value in also_levels must be a CEFR level, appear once, and be higher than
    main_level. also_levels without a main_level is refused.
    """
    main = Level(main_level) if main_level is not None else None
    also = parse_levels(also_levels)
    if also and main is None:
        raise ValueError("also_levels needs a main_level")
    if len(set(also)) != len(also):
        raise ValueError(f"also_levels has duplicates: {levels_to_db(also)}")
    if main is not None:
        lower = [level for level in also if level.rank <= main.rank]
        if lower:
            raise ValueError(
                f"also_levels must be higher than main_level {main}: {levels_to_db(tuple(lower))}"
            )
    return main, tuple(sorted(also, key=lambda level: level.rank))


def _from_row(row: sqlite3.Row) -> Topic:
    return Topic(
        id=row["id"],
        code=row["code"],
        name=row["name"],
        description=row["description"],
        type=TopicType(row["type"]),
        category=row["category"],
        main_level=Level(row["main_level"]) if row["main_level"] is not None else None,
        also_levels=parse_levels(row["also_levels"]),
        unit=row["unit"],
        order_in_program=row["order_in_program"],
        source_program=row["source_program"],
        source_ref=row["source_ref"],
    )


def create(
    conn: sqlite3.Connection,
    *,
    name: str,
    type: TopicType | str,
    description: str = "",
    code: str | None = None,
    category: str | None = None,
    main_level: Level | str | None = None,
    also_levels: str | Iterable[Level | str] | None = None,
    unit: str | None = None,
    order_in_program: int | None = None,
    source_program: str | None = None,
    source_ref: str | None = None,
) -> Topic:
    topic_type = TopicType(type)
    main, also = check_levels(main_level, also_levels)
    item_id = new_id()
    with transaction(conn):
        conn.execute(
            "INSERT INTO learning_item (id, item_type) VALUES (?, ?)",
            (item_id, ItemType.TOPIC.value),
        )
        conn.execute(
            f"INSERT INTO topic ({_COLUMNS}) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                item_id,
                code,
                name,
                description,
                topic_type.value,
                category,
                main.value if main else None,
                levels_to_db(also),
                unit,
                order_in_program,
                source_program,
                source_ref,
            ),
        )
    return require(get(conn, item_id), "topic")


def get(conn: sqlite3.Connection, topic_id: str) -> Topic | None:
    row = conn.execute(f"{_SELECT} WHERE id = ?", (topic_id,)).fetchone()
    return _from_row(row) if row else None


def get_by_code(conn: sqlite3.Connection, code: str) -> Topic | None:
    row = conn.execute(f"{_SELECT} WHERE code = ?", (code,)).fetchone()
    return _from_row(row) if row else None


def list_all(
    conn: sqlite3.Connection,
    *,
    type: TopicType | str | None = None,
    category: str | None = None,
    main_level: Level | str | None = None,
    level: Level | str | None = None,
    source_program: str | None = None,
) -> list[Topic]:
    """List Topics in program order.

    main_level matches only the level where a Topic is first taught; level matches
    Topics taught at that level at all (main_level or one of also_levels).
    """
    clauses: list[str] = []
    params: list[Any] = []
    if type is not None:
        clauses.append("type = ?")
        params.append(TopicType(type).value)
    if category is not None:
        clauses.append("category = ?")
        params.append(category)
    if main_level is not None:
        clauses.append("main_level = ?")
        params.append(Level(main_level).value)
    if level is not None:
        value = Level(level).value
        clauses.append("(main_level = ? OR ';' || also_levels || ';' LIKE ?)")
        params.extend([value, f"%;{value};%"])
    if source_program is not None:
        clauses.append("source_program = ?")
        params.append(source_program)
    where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"{_SELECT}{where} ORDER BY order_in_program IS NULL, order_in_program, id", params
    ).fetchall()
    return [_from_row(row) for row in rows]


def update(conn: sqlite3.Connection, topic_id: str, **fields: Any) -> Topic:
    unknown = set(fields) - _UPDATABLE
    if unknown:
        raise ValueError(f"Cannot update topic fields: {sorted(unknown)}")
    if "type" in fields:
        fields["type"] = TopicType(fields["type"])
    if "main_level" in fields or "also_levels" in fields:
        current = require(get(conn, topic_id), "topic")
        main, also = check_levels(
            fields.get("main_level", current.main_level),
            fields.get("also_levels", current.also_levels),
        )
        if "main_level" in fields:
            fields["main_level"] = main.value if main else None
        if "also_levels" in fields:
            fields["also_levels"] = levels_to_db(also)
    update_row(conn, "topic", "id", topic_id, fields, _UPDATABLE)
    return require(get(conn, topic_id), "topic")
