"""Shared pytest fixtures."""

from datetime import UTC, datetime

import pytest

from rosetta_flame.db import open_database
from rosetta_flame.db.repositories import exercises, texts, topics, weak_spots
from rosetta_flame.models.enums import ExerciseSource, ExerciseType, TopicType


@pytest.fixture
def conn():
    """A fresh in-memory database with every migration applied."""
    connection = open_database(":memory:")
    yield connection
    connection.close()


@pytest.fixture
def missing_id():
    """A well-formed id that no row has."""
    return "00000000-0000-4000-8000-000000000000"


@pytest.fixture
def now():
    return datetime(2026, 11, 8, 19, 0, tzinfo=UTC)


@pytest.fixture
def topic(conn):
    return topics.create(
        conn,
        name="Quantifiers",
        type=TopicType.GRAMMAR,
        main_level="B1",
        unit="3",
        order_in_program=30,
        source_program="Test Program",
    )


@pytest.fixture
def weak_spot(conn, now, topic):
    return weak_spots.create(conn, name="much/many", created_at=now, topic_ids=[topic.id])


@pytest.fixture
def submitted_text(conn, now):
    return texts.create(conn, content="I have many water.", submitted_at=now)


@pytest.fixture
def exercise(conn, now, weak_spot):
    return exercises.create(
        conn,
        learning_item_id=weak_spot.id,
        type=ExerciseType.FILL_IN_THE_BLANK,
        prompt="I don't have ___ water.",
        answer="much",
        source=ExerciseSource.GENERIC,
        created_at=now,
    )
