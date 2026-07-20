"""Data-driven emotion effects for classified conversation contexts."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .config import PLUGIN_CONFIG
from .state import EMOTIONS, EmotionState


DEFAULT_SWING_CONFIG = PLUGIN_CONFIG.get(
    "mood_swing",
    {"active_preset": "default", "presets": {"default": {"formula": "fixed"}}},
)


class UnknownEventError(KeyError):
    """Raised when an event name is not present in the configured rules."""


@dataclass(frozen=True)
class EventRules:
    """A collection of named, bounded emotion deltas."""

    rules: Mapping[str, Mapping[str, float]]
    swing_config: Mapping[str, Any] = field(
        default_factory=lambda: {
            "active_preset": "default",
            "presets": {"default": {"formula": "fixed"}},
        }
    )

    @classmethod
    def from_json_file(cls, path: str | Path) -> "EventRules":
        rules_path = Path(path)
        with rules_path.open(encoding="utf-8") as file:
            rules = json.load(file)
        if not isinstance(rules, dict):
            raise ValueError("Emotion rules JSON must contain an object")

        return cls(rules, DEFAULT_SWING_CONFIG)

    def _delta_multiplier(self, *, confidence: float, intensity: float) -> float:
        preset_name = self.swing_config.get("active_preset", "default")
        presets = self.swing_config.get("presets", {})
        preset = presets.get(preset_name, presets.get("default", {"formula": "fixed"}))
        formula = preset.get("formula", "fixed")
        if formula == "fixed":
            return 1.0
        if formula == "base_times_sum":
            confidence = max(0.0, min(1.0, float(confidence)))
            intensity = max(0.0, min(1.0, float(intensity)))
            return (1.0 + confidence) + (1.0 + intensity)
        raise ValueError(f"Unknown mood swing formula: {formula}")

    def apply(
        self,
        state: EmotionState,
        event_name: str,
        *,
        confidence: float = 1.0,
        intensity: float = 0.0,
    ) -> EmotionState:
        try:
            deltas = self.rules[event_name]
        except KeyError as error:
            raise UnknownEventError(f"Unknown emotion event: {event_name}") from error

        multiplier = self._delta_multiplier(confidence=confidence, intensity=intensity)
        values = state.to_dict()
        for emotion, delta in deltas.items():
            if emotion not in EMOTIONS:
                raise ValueError(f"Unknown emotion in event rule: {emotion}")
            values[emotion] += float(delta) * multiplier
        return EmotionState.from_dict(values)
