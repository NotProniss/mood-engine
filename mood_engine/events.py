"""Data-driven emotion event rules."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .state import EMOTIONS, EmotionState


class UnknownEventError(KeyError):
    """Raised when an event name is not present in the configured rules."""


@dataclass(frozen=True)
class EventContext:
    """Context used to appraise an event without changing its name."""

    absence_explained: bool = False


@dataclass(frozen=True)
class EventRules:
    """A collection of named emotion deltas."""

    rules: Mapping[str, Mapping[str, float]]

    @classmethod
    def from_json_file(cls, path: str | Path) -> "EventRules":
        with Path(path).open(encoding="utf-8") as file:
            rules = json.load(file)
        if not isinstance(rules, dict):
            raise ValueError("Emotion rules JSON must contain an object")
        return cls(rules)

    def apply(
        self,
        state: EmotionState,
        event_name: str,
        context: EventContext | None = None,
    ) -> EmotionState:
        try:
            deltas = self.rules[event_name]
        except KeyError as error:
            raise UnknownEventError(f"Unknown emotion event: {event_name}") from error

        context = context or EventContext()
        values = state.to_dict()
        for emotion, delta in deltas.items():
            if emotion not in EMOTIONS:
                raise ValueError(f"Unknown emotion in event rule: {emotion}")
            if event_name == "long_absence" and context.absence_explained:
                delta *= 0.25
            values[emotion] += delta
        return EmotionState.from_dict(values)
