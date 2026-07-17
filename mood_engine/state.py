"""Core state types for the Hermes affect prototype."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass


EMOTIONS = ("joy", "sadness", "anger", "fear", "disgust")


def _clamp(value: float) -> float:
    return max(0, min(100, value))


@dataclass
class EmotionState:
    """Bounded intensity values for the prototype's five emotions."""

    joy: float = 0
    sadness: float = 0
    anger: float = 0
    fear: float = 0
    disgust: float = 0

    def __post_init__(self) -> None:
        for emotion in EMOTIONS:
            setattr(self, emotion, _clamp(getattr(self, emotion)))

    def to_dict(self) -> dict[str, float]:
        """Return precise values for internal processing and persistence."""
        return {emotion: getattr(self, emotion) for emotion in EMOTIONS}

    def to_display_dict(self) -> dict[str, int]:
        """Return whole-number values, rounded down for display."""
        return {emotion: math.floor(getattr(self, emotion)) for emotion in EMOTIONS}

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    def to_display_json(self) -> str:
        return json.dumps(self.to_display_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, values: dict[str, float]) -> "EmotionState":
        missing = set(EMOTIONS) - values.keys()
        if missing:
            raise ValueError(f"Missing emotion values: {', '.join(sorted(missing))}")
        return cls(**{emotion: values[emotion] for emotion in EMOTIONS})

    @classmethod
    def from_json(cls, payload: str) -> "EmotionState":
        values = json.loads(payload)
        if not isinstance(values, dict):
            raise ValueError("Emotion state JSON must contain an object")
        return cls.from_dict(values)
