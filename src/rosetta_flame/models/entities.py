"""Plain data classes for the entities stored in the database."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from rosetta_flame.models.enums import (
    ExerciseSource,
    ExerciseType,
    ItemType,
    Level,
    Status,
    TopicType,
)


@dataclass(frozen=True, slots=True)
class LearningItem:
    """A Topic or a Weak Spot, seen through the shared learning_item table."""

    id: str
    item_type: ItemType
    name: str
    description: str


@dataclass(frozen=True, slots=True)
class TopicTypeInfo:
    """A row of the topic_type lookup table: a type and its description."""

    name: TopicType
    description: str


@dataclass(frozen=True, slots=True)
class Topic:
    id: str
    name: str
    description: str
    type: TopicType
    code: str | None = None
    category: str | None = None
    main_level: Level | None = None
    also_levels: tuple[Level, ...] = ()
    unit: str | None = None
    order_in_program: int | None = None
    source_program: str | None = None
    source_ref: str | None = None


@dataclass(frozen=True, slots=True)
class WeakSpot:
    id: str
    name: str
    description: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class ReviewState:
    learning_item_id: str
    status: Status
    next_review_date: date | None
    interval_step: int
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class Text:
    id: str
    content: str
    submitted_at: datetime


@dataclass(frozen=True, slots=True)
class Mistake:
    id: str
    text_id: str
    weak_spot_id: str
    original: str
    correction: str
    explanation: str
    dismissed: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class Exercise:
    id: str
    learning_item_id: str
    type: ExerciseType
    prompt: str
    answer: str
    source: ExerciseSource
    created_at: datetime
    options: tuple[str, ...] | None = None
    mistake_id: str | None = None


@dataclass(frozen=True, slots=True)
class Attempt:
    id: str
    exercise_id: str
    correct: bool
    answered_at: datetime
    local_date: date
