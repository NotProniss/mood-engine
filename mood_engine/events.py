"""Data-driven emotion effects for classified conversation contexts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .state import EMOTIONS, EmotionState


class UnknownEventError(KeyError):
    """Raised when an event name is not present in the configured rules."""


@dataclass(frozen=True)
class EventRules:
    """A collection of named, bounded emotion deltas."""

    rules: Mapping[str, Mapping[str, float]]

    @classmethod
    def from_json_file(cls, path: str | Path) -> "EventRules":
        with Path(path).open(encoding="utf-8") as file:
            rules = json.load(file)
        if not isinstance(rules, dict):
            raise ValueError("Emotion rules JSON must contain an object")
        return cls(rules)

    def apply(self, state: EmotionState, event_name: str) -> EmotionState:
        try:
            deltas = self.rules[event_name]
        except KeyError as error:
            raise UnknownEventError(f"Unknown emotion event: {event_name}") from error

        values = state.to_dict()
        for emotion, delta in deltas.items():
            if emotion not in EMOTIONS:
                raise ValueError(f"Unknown emotion in event rule: {emotion}")
            values[emotion] += delta
        return EmotionState.from_dict(values)
