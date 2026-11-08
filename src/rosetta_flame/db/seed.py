"""Load the topic seed (resources/topics_seed.csv) into the database.

The import is safe to run again: Topics are matched by their ``code`` (the seed's
``id`` column), new ones are created, changed ones are updated and nothing is deleted.
The whole file is validated before anything is written, and the writes run in one
transaction, so a failed import leaves the database as it was.
"""

from __future__ import annotations

import csv
import io
import re
import sqlite3
from dataclasses import dataclass, field
from importlib import resources
from typing import Any

from rosetta_flame.db.connection import transaction
from rosetta_flame.db.repositories import topics
from rosetta_flame.models.entities import Topic
from rosetta_flame.models.enums import Level, TopicType

RESOURCES_PACKAGE = "rosetta_flame.db.resources"
TOPIC_SEED_FILE = "topics_seed.csv"
TOPIC_SEED_COLUMNS = (
    "id",
    "name",
    "type",
    "category",
    "main_level",
    "also_levels",
    "order_in_program",
    "source_ref",
    "description",
)
_CODE_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class SeedError(ValueError):
    """The seed file has problems. ``problems`` lists every one, with its line number."""

    def __init__(self, problems: list[str]) -> None:
        self.problems = problems
        super().__init__(f"Seed file has {len(problems)} problem(s):\n" + "\n".join(problems))


@dataclass(frozen=True, slots=True)
class TopicSeedRow:
    """One validated row of the seed file."""

    code: str
    name: str
    type: TopicType
    category: str | None
    main_level: Level
    also_levels: tuple[Level, ...]
    order_in_program: int
    source_ref: str | None
    description: str

    def fields(self) -> dict[str, Any]:
        """The Topic fields this row sets, as accepted by the topics repository."""
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "category": self.category,
            "main_level": self.main_level,
            "also_levels": self.also_levels,
            "order_in_program": self.order_in_program,
            "source_ref": self.source_ref,
        }


@dataclass(slots=True)
class SeedReport:
    """What an import did, or would do in a dry run. Lists hold Topic codes."""

    created: list[str] = field(default_factory=list)
    updated: list[str] = field(default_factory=list)
    unchanged: list[str] = field(default_factory=list)
    not_in_seed: list[str] = field(default_factory=list)
    dry_run: bool = False


def read_topic_seed_text() -> str:
    """The packaged seed file's content."""
    return resources.files(RESOURCES_PACKAGE).joinpath(TOPIC_SEED_FILE).read_text("utf-8")


def parse_topic_seed(text: str) -> list[TopicSeedRow]:
    """Parse and validate the whole file. Raises SeedError listing every problem."""
    reader = csv.DictReader(io.StringIO(text))
    header = reader.fieldnames or []
    missing = [column for column in TOPIC_SEED_COLUMNS if column not in header]
    extra = [column for column in header if column not in TOPIC_SEED_COLUMNS]
    if missing or extra:
        problems = []
        if missing:
            problems.append(f"line 1: missing column(s): {', '.join(missing)}")
        if extra:
            problems.append(f"line 1: unknown column(s): {', '.join(extra)}")
        raise SeedError(problems)

    rows: list[TopicSeedRow] = []
    problems: list[str] = []
    seen_codes: dict[str, int] = {}
    seen_names: dict[str, int] = {}
    seen_orders: dict[int, int] = {}
    for line, raw in enumerate(reader, start=2):
        values = {key: (value or "").strip() for key, value in raw.items() if key is not None}
        row_problems: list[str] = []

        code = values["id"]
        if not _CODE_PATTERN.match(code):
            row_problems.append(f"id {code!r} must be lowercase words joined by '-'")
        elif code in seen_codes:
            row_problems.append(f"id {code!r} repeats line {seen_codes[code]}")

        name = values["name"]
        if not name:
            row_problems.append("name is empty")
        elif name.casefold() in seen_names:
            row_problems.append(f"name {name!r} repeats line {seen_names[name.casefold()]}")

        if not values["description"]:
            row_problems.append("description is empty")

        topic_type: TopicType | None = None
        try:
            topic_type = TopicType(values["type"])
        except ValueError:
            row_problems.append(
                f"type {values['type']!r} is not one of {[t.value for t in TopicType]}"
            )

        main_level: Level | None = None
        also_levels: tuple[Level, ...] = ()
        if not values["main_level"]:
            row_problems.append("main_level is empty")
        else:
            try:
                checked_main, also_levels = topics.check_levels(
                    values["main_level"], values["also_levels"]
                )
                main_level = checked_main
            except ValueError as error:
                row_problems.append(str(error))

        order: int | None = None
        try:
            order = int(values["order_in_program"])
            if order < 1:
                raise ValueError
            if order in seen_orders:
                row_problems.append(f"order_in_program {order} repeats line {seen_orders[order]}")
        except ValueError:
            row_problems.append(
                f"order_in_program {values['order_in_program']!r} must be a positive whole number"
            )

        if row_problems:
            problems.extend(f"line {line}: {problem}" for problem in row_problems)
            continue
        assert topic_type is not None and main_level is not None and order is not None
        seen_codes[code] = line
        seen_names[name.casefold()] = line
        seen_orders[order] = line
        rows.append(
            TopicSeedRow(
                code=code,
                name=name,
                type=topic_type,
                category=values["category"] or None,
                main_level=main_level,
                also_levels=also_levels,
                order_in_program=order,
                source_ref=values["source_ref"] or None,
                description=values["description"],
            )
        )
    if problems:
        raise SeedError(problems)
    if not rows:
        raise SeedError(["the seed file has no rows"])
    return rows


def _changes(topic: Topic, row: TopicSeedRow) -> dict[str, Any]:
    """The fields where the stored Topic differs from the seed row."""
    return {name: value for name, value in row.fields().items() if getattr(topic, name) != value}


def import_topics(
    conn: sqlite3.Connection, *, text: str | None = None, dry_run: bool = False
) -> SeedReport:
    """Create or update Topics from the seed. ``text`` defaults to the packaged file.

    With ``dry_run`` the file is validated and the report says what would change, but
    nothing is written.
    """
    rows = parse_topic_seed(read_topic_seed_text() if text is None else text)
    report = SeedReport(dry_run=dry_run)
    plan: list[tuple[TopicSeedRow, Topic | None, dict[str, Any]]] = []
    for row in rows:
        existing = topics.get_by_code(conn, row.code)
        if existing is None:
            report.created.append(row.code)
            plan.append((row, None, {}))
            continue
        changes = _changes(existing, row)
        if changes:
            report.updated.append(row.code)
            plan.append((row, existing, changes))
        else:
            report.unchanged.append(row.code)

    seed_codes = {row.code for row in rows}
    report.not_in_seed = sorted(
        topic.code
        for topic in topics.list_all(conn)
        if topic.code is not None and topic.code not in seed_codes
    )

    if not dry_run:
        with transaction(conn):
            for row, existing, changes in plan:
                if existing is None:
                    topics.create(conn, code=row.code, **row.fields())
                else:
                    topics.update(conn, existing.id, **changes)
    return report
