import sqlite3

import pytest

from rosetta_flame.db.repositories import learning_items, topics, weak_spots
from rosetta_flame.models.enums import ItemType


def test_create_links_topics_and_registers_learning_item(conn, topic, weak_spot):
    assert weak_spots.get(conn, weak_spot.id) == weak_spot
    assert weak_spots.topic_ids(conn, weak_spot.id) == [topic.id]
    item = learning_items.get(conn, weak_spot.id)
    assert item.item_type is ItemType.WEAK_SPOT


def test_create_is_all_or_nothing(conn, now, missing_id):
    before = len(learning_items.list_all(conn))
    with pytest.raises(sqlite3.IntegrityError):
        weak_spots.create(conn, name="x", created_at=now, topic_ids=[missing_id])
    assert len(learning_items.list_all(conn)) == before
    assert weak_spots.list_all(conn) == []


def test_link_and_unlink_topics(conn, now, topic, weak_spot):
    other = topics.create(conn, name="Articles", type="grammar")
    weak_spots.link_topic(conn, weak_spot.id, other.id)
    weak_spots.link_topic(conn, weak_spot.id, other.id)  # linking twice is harmless
    assert weak_spots.topic_ids(conn, weak_spot.id) == sorted([topic.id, other.id])
    weak_spots.unlink_topic(conn, weak_spot.id, other.id)
    assert weak_spots.topic_ids(conn, weak_spot.id) == [topic.id]


def test_linking_a_missing_topic_fails(conn, weak_spot, missing_id):
    with pytest.raises(sqlite3.IntegrityError):
        weak_spots.link_topic(conn, weak_spot.id, missing_id)


def test_list_for_topic(conn, now, topic, weak_spot):
    unrelated = weak_spots.create(conn, name="other", created_at=now)
    assert [w.id for w in weak_spots.list_for_topic(conn, topic.id)] == [weak_spot.id]
    assert unrelated.id not in [w.id for w in weak_spots.list_for_topic(conn, topic.id)]


def test_update(conn, weak_spot):
    updated = weak_spots.update(conn, weak_spot.id, name="much / many", description="Countable")
    assert (updated.name, updated.description) == ("much / many", "Countable")
    with pytest.raises(ValueError):
        weak_spots.update(conn, weak_spot.id, created_at=None)


def test_learning_items_lists_both_kinds(conn, topic, weak_spot):
    items = learning_items.list_all(conn)
    assert [(i.id, i.item_type) for i in items] == [
        (topic.id, ItemType.TOPIC),
        (weak_spot.id, ItemType.WEAK_SPOT),
    ]
    only_weak = learning_items.list_all(conn, item_type="weak_spot")
    assert [i.id for i in only_weak] == [weak_spot.id]
