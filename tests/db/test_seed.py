"""The topic seed import: validation, upsert by code, dry run and rollback."""

import pytest

from rosetta_flame.db.repositories import topics
from rosetta_flame.db.seed import (
    SeedError,
    import_topics,
    parse_topic_seed,
    read_topic_seed_text,
)
from rosetta_flame.models.enums import Level, TopicType

HEADER = "id,name,type,category,main_level,also_levels,order_in_program,source_ref,description\n"


def seed(*rows: str) -> str:
    return HEADER + "".join(f"{row}\n" for row in rows)


ARTICLES = 'g-articles,"Articles",grammar,"Articles",A1,A2,1,135,"a, an and the."'
FOOD = 'v-food,"Food and drink",vocabulary,,A1,,2,,"Foods and drinks."'


def test_packaged_seed_is_valid():
    rows = parse_topic_seed(read_topic_seed_text())
    assert len(rows) == 176
    assert {row.type for row in rows} == set(TopicType)
    assert [row.order_in_program for row in rows] == list(range(1, 177))


def test_first_import_creates_every_topic(conn):
    report = import_topics(conn)
    assert len(report.created) == 176
    assert report.updated == report.unchanged == report.not_in_seed == []
    past_simple = topics.get_by_code(conn, "g-past-simple")
    assert past_simple is not None
    assert past_simple.type is TopicType.GRAMMAR
    assert past_simple.main_level is Level.A1
    assert past_simple.also_levels == (Level.A2, Level.B1)
    assert past_simple.source_ref == "67"


def test_second_import_changes_nothing(conn):
    import_topics(conn)
    report = import_topics(conn)
    assert report.created == report.updated == []
    assert len(report.unchanged) == 176
    assert len(topics.list_all(conn)) == 176


def test_changed_row_updates_the_topic_and_keeps_its_id(conn):
    import_topics(conn, text=seed(ARTICLES, FOOD))
    before = topics.get_by_code(conn, "g-articles")
    edited = ARTICLES.replace("A1,A2", "A1,A2;B1").replace('"a, an and the."', '"Articles."')
    report = import_topics(conn, text=seed(edited, FOOD))
    assert report.updated == ["g-articles"]
    assert report.unchanged == ["v-food"]
    after = topics.get_by_code(conn, "g-articles")
    assert after.id == before.id
    assert after.also_levels == (Level.A2, Level.B1)
    assert after.description == "Articles."


def test_topic_removed_from_seed_is_kept_and_reported(conn):
    import_topics(conn, text=seed(ARTICLES, FOOD))
    topics.create(conn, name="My own topic", type="lexical")
    report = import_topics(conn, text=seed(ARTICLES))
    assert report.not_in_seed == ["v-food"]
    assert topics.get_by_code(conn, "v-food") is not None
    assert len(topics.list_all(conn)) == 3


def test_empty_optional_fields_become_none(conn):
    import_topics(conn, text=seed(FOOD))
    food = topics.get_by_code(conn, "v-food")
    assert (food.category, food.source_ref, food.also_levels) == (None, None, ())


def test_dry_run_reports_without_writing(conn):
    report = import_topics(conn, dry_run=True)
    assert report.dry_run
    assert len(report.created) == 176
    assert topics.list_all(conn) == []


def test_every_bad_row_is_reported_and_nothing_is_written(conn):
    text = seed(
        ARTICLES,
        'g-articles,"Other",grammar,,A1,,2,,"Duplicate id."',
        'g-bad-type,"Spelling",spelling,,A1,,3,,"Unknown type."',
        'g-bad-levels,"Levels",grammar,,B1,A2,4,,"Lower also level."',
        'g-no-order,"No order",grammar,,A1,,x,,"Bad order."',
        'g-empty,"",grammar,,,,6,,""',
    )
    with pytest.raises(SeedError) as caught:
        import_topics(conn, text=text)
    problems = "\n".join(caught.value.problems)
    assert "line 3: id 'g-articles' repeats line 2" in problems
    assert "line 4: type 'spelling'" in problems
    assert "line 5: also_levels must be higher than main_level B1" in problems
    assert "line 6: order_in_program 'x'" in problems
    assert "line 7: name is empty" in problems
    assert "line 7: description is empty" in problems
    assert "line 7: main_level is empty" in problems
    assert topics.list_all(conn) == []


def test_missing_column_is_reported():
    with pytest.raises(SeedError, match="missing column"):
        parse_topic_seed("id,name,type\ng-x,X,grammar\n")


def test_failure_midway_rolls_back_the_whole_import(conn, monkeypatch):
    real_create = topics.create
    calls = {"count": 0}

    def failing_create(*args, **kwargs):
        calls["count"] += 1
        if calls["count"] == 10:
            raise RuntimeError("boom")
        return real_create(*args, **kwargs)

    monkeypatch.setattr(topics, "create", failing_create)
    with pytest.raises(RuntimeError):
        import_topics(conn)
    assert topics.list_all(conn) == []
