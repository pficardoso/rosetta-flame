"""Fixed sets of values used across the app."""

from __future__ import annotations

from enum import StrEnum


class Status(StrEnum):
    NEW = "New"
    LEARNING = "Learning"
    REVIEWING = "Reviewing"
    MASTERED = "Mastered"


class ItemType(StrEnum):
    """Kinds of learning item."""

    TOPIC = "topic"
    WEAK_SPOT = "weak_spot"


class TopicType(StrEnum):
    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"


class ExerciseType(StrEnum):
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    CORRECT_THE_SENTENCE = "correct_the_sentence"
    MULTIPLE_CHOICE = "multiple_choice"
    REWRITE_THE_SENTENCE = "rewrite_the_sentence"


class ExerciseSource(StrEnum):
    MISTAKE = "mistake"
    GENERIC = "generic"
