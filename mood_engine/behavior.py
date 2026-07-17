"""Deterministic behavior signals derived from the five-emotion state."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .state import EmotionState


def _clamp(value: float) -> float:
    return max(-100.0, min(100.0, value))


@dataclass(frozen=True)
class BehaviorSignals:
    """Inspectable signed -100 to +100 signals for a later response layer."""

    warmth: float
    energy: float
    caution: float
    initiative: float
    reflection: float

    def to_dict(self) -> dict[str, int]:
        """Return whole-number values suitable for display or prompt context."""
        return {
            "warmth": math.floor(self.warmth),
            "energy": math.floor(self.energy),
            "caution": math.floor(self.caution),
            "initiative": math.floor(self.initiative),
            "reflection": math.floor(self.reflection),
        }


def derive_behavior_signals(state: EmotionState) -> BehaviorSignals:
    """Translate emotion intensities into bounded behavior guidance signals."""
    return BehaviorSignals(
        warmth=_clamp(state.joy - state.sadness - state.anger - state.disgust),
        energy=_clamp(state.joy - state.sadness - state.fear),
        caution=_clamp(state.fear + state.anger + state.disgust),
        initiative=_clamp(state.joy - state.sadness - state.fear - state.anger),
        reflection=_clamp(state.sadness + state.fear),
    )
