import pytest

from rosetta_flame.db.repositories import learning_items, topics
from rosetta_flame.models.enums import ItemType, TopicType


def test_create_and_get(conn, topic):
    assert topics.get(conn, topic.id) == topic
    assert topic.type is TopicType.GRAMMAR
    assert (topic.level, topic.unit, topic.order_in_program) == ("B1", "3", 30)


def test_create_registers_a_topic_learning_item(conn, topic):
    item = learning_items.get(conn, topic.id)
    assert item is not None
    assert item.item_type is ItemType.TOPIC
    assert item.name == "Quantifiers"


def test_get_missing_returns_none(conn, missing_id):
    assert topics.get(conn, missing_id) is None


def test_invalid_type_is_rejected_and_nothing_is_stored(conn):
    with pytest.raises(ValueError):
        topics.create(conn, name="x", type="spelling")
    assert learning_items.list_all(conn) == []


def test_list_follows_program_order_and_filters(conn):
    articles = topics.create(conn, name="Articles", type="grammar", level="A2", order_in_program=10)
    food = topics.create(conn, name="Food", type="vocabulary", level="A2", order_in_program=20)
    loose = topics.create(conn, name="Loose", type="vocabulary")
    assert [t.id for t in topics.list_all(conn)] == [articles.id, food.id, loose.id]
    assert [t.id for t in topics.list_all(conn, type="vocabulary")] == [food.id, loose.id]
    assert [t.id for t in topics.list_all(conn, level="A2")] == [articles.id, food.id]


def test_update(conn, topic):
    updated = topics.update(conn, topic.id, name="Quantifiers 2", type="vocabulary", unit=None)
    assert updated.name == "Quantifiers 2"
    assert updated.type is TopicType.VOCABULARY
    assert updated.unit is None


def test_update_rejects_unknown_field_and_missing_topic(conn, topic, missing_id):
    with pytest.raises(ValueError):
        topics.update(conn, topic.id, id=5)
    with pytest.raises(LookupError):
        topics.update(conn, missing_id, name="x")
