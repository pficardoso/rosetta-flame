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
    """Kinds of Topic. Must match the rows of the topic_type table (a test checks this)."""

    GRAMMAR = "grammar"
    VOCABULARY = "vocabulary"
    LEXICAL = "lexical"
    FUNCTIONS = "functions"


class Level(StrEnum):
    """CEFR levels, from lowest to highest. Definition order is level order."""

    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

    @property
    def rank(self) -> int:
        return list(Level).index(self)


class ExerciseType(StrEnum):
    FILL_IN_THE_BLANK = "fill_in_the_blank"
    CORRECT_THE_SENTENCE = "correct_the_sentence"
    MULTIPLE_CHOICE = "multiple_choice"
    REWRITE_THE_SENTENCE = "rewrite_the_sentence"


class ExerciseSource(StrEnum):
    MISTAKE = "mistake"
    GENERIC = "generic"
