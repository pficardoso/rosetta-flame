from datetime import UTC, date, datetime

import pytest

from rosetta_flame.db.repositories import attempts, exercises, mistakes
from rosetta_flame.models.enums import ExerciseSource, ExerciseType


def test_exercise_round_trip_with_options(conn, now, weak_spot):
    exercise = exercises.create(
        conn, learning_item_id=weak_spot.id, type=ExerciseType.MULTIPLE_CHOICE,
        prompt="I don't have ___ water.", answer="much", options=["much", "many", "few"],
        source=ExerciseSource.GENERIC, created_at=now,
    )
    assert exercises.get(conn, exercise.id) == exercise
    assert exercise.options == ("much", "many", "few")
    assert exercises.list_for_item(conn, weak_spot.id) == [exercise]


def test_exercise_without_options_has_none(exercise):
    assert exercise.options is None
    assert exercise.mistake_id is None


def test_exercise_can_come_from_a_mistake(conn, now, submitted_text, weak_spot):
    mistake = mistakes.create(
        conn, text_id=submitted_text.id, weak_spot_id=weak_spot.id, original="many water",
        correction="much water", created_at=now,
    )
    exercise = exercises.create(
        conn, learning_item_id=weak_spot.id, type="correct_the_sentence",
        prompt="I have many water.", answer="I have much water.",
        source="mistake", mistake_id=mistake.id, created_at=now,
    )
    assert exercise.source is ExerciseSource.MISTAKE
    assert exercises.list_for_mistake(conn, mistake.id) == [exercise]


def test_invalid_exercise_type_is_rejected(conn, now, weak_spot):
    with pytest.raises(ValueError):
        exercises.create(
            conn, learning_item_id=weak_spot.id, type="essay", prompt="p", answer="a",
            source="generic", created_at=now,
        )


def test_record_stores_utc_time_and_the_lisbon_day(conn, exercise):
    answered = datetime(2026, 7, 1, 23, 30, tzinfo=UTC)  # 00:30 on 2 July in Lisbon (summer)
    attempt = attempts.record(conn, exercise_id=exercise.id, correct=True, answered_at=answered)
    assert attempt.local_date == date(2026, 7, 2)
    assert attempt.answered_at == answered
    assert attempt.correct is True


def test_local_day_follows_the_given_timezone(conn, exercise):
    answered = datetime(2026, 7, 1, 23, 30, tzinfo=UTC)
    attempt = attempts.record(
        conn, exercise_id=exercise.id, correct=False, answered_at=answered, tz="America/New_York"
    )
    assert attempt.local_date == date(2026, 7, 1)


def test_naive_datetime_is_rejected(conn, exercise):
    with pytest.raises(ValueError):
        attempts.record(
            conn, exercise_id=exercise.id, correct=True, answered_at=datetime(2026, 11, 1, 10, 0)
        )


def _record(conn, exercise, day, hour, correct):
    return attempts.record(
        conn, exercise_id=exercise.id, correct=correct,
        answered_at=datetime(2026, 11, day, hour, 0, tzinfo=UTC),
    )


def test_history_is_ordered_by_time_across_exercises(conn, now, weak_spot, exercise):
    second = exercises.create(
        conn, learning_item_id=weak_spot.id, type="fill_in_the_blank", prompt="p2",
        answer="a2", source="generic", created_at=now,
    )
    late = _record(conn, second, 3, 9, True)
    early = _record(conn, exercise, 1, 9, False)
    middle = _record(conn, exercise, 2, 9, True)
    history = attempts.list_for_item(conn, weak_spot.id)
    assert [a.id for a in history] == [early.id, middle.id, late.id]
    assert [a.id for a in attempts.list_for_exercise(conn, exercise.id)] == [early.id, middle.id]


def test_correct_days_are_distinct_and_ignore_wrong_answers(conn, exercise):
    _record(conn, exercise, 1, 9, False)
    _record(conn, exercise, 1, 10, True)
    _record(conn, exercise, 1, 11, True)
    _record(conn, exercise, 2, 9, False)
    _record(conn, exercise, 3, 9, True)
    assert attempts.correct_days(conn, exercise.learning_item_id) == [
        date(2026, 11, 1),
        date(2026, 11, 3),
    ]


def test_history_only_includes_the_requested_item(conn, now, topic, exercise):
    other = exercises.create(
        conn, learning_item_id=topic.id, type="fill_in_the_blank", prompt="p", answer="a",
        source="generic", created_at=now,
    )
    _record(conn, exercise, 1, 9, True)
    _record(conn, other, 1, 9, True)
    assert len(attempts.list_for_item(conn, exercise.learning_item_id)) == 1
    assert len(attempts.list_for_item(conn, topic.id)) == 1
