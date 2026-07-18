"""Focused-emotion response guidance."""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
from pathlib import Path

from .state import EmotionState


TONE_PROFILES_PATH = Path(__file__).parents[1] / "config" / "tone_profiles.json"
with TONE_PROFILES_PATH.open(encoding="utf-8") as file:
    TONE_PROFILES = json.load(file)


@dataclass(frozen=True)
class ResponseGuidance:
    """The complete prompt-facing mood guidance."""

    focus: str
    intensity: float
    tone: str
    behavior: str | None = None

    def to_dict(self) -> dict[str, int | str]:
        values: dict[str, int | str] = {
            "focus": self.focus,
            "intensity": math.floor(self.intensity),
            "tone": self.tone,
        }
        if self.behavior:
            values["behavior"] = self.behavior
        return values

    def to_prompt_context(self) -> str:
        """Return only the intentionally exposed prompt-facing guidance."""
        context = f"focus={self.focus}; tone={self.tone}"
        if self.behavior:
            context += f"; behavior={self.behavior}"
        return context


def _focused_emotion(state: EmotionState) -> tuple[str, float]:
    focus, intensity = max(state.to_dict().items(), key=lambda item: item[1])
    if intensity <= 0:
        return "neutral", 0.0
    return focus, intensity


def _joy_tone(intensity: float) -> str:
    if intensity >= 75:
        return "ecstatic"
    if intensity >= 50:
        return "excited"
    if intensity >= 25:
        return "happy"
    return "content"


def _focused_tone(focus: str, intensity: float) -> str:
    if focus == "joy":
        return _joy_tone(intensity)
    if focus == "anger":
        if intensity >= 75:
            return "scathing"
        if intensity >= 50:
            return "aggressive"
        if intensity >= 25:
            return "irritated"
        return "annoyed"
    if focus == "sadness":
        if intensity >= 75:
            return "sorrowful"
        if intensity >= 50:
            return "heavy"
        if intensity >= 25:
            return "sad"
        return "downcast"
    if focus == "fear":
        if intensity >= 75:
            return "horrified"
        if intensity >= 50:
            return "anxious"
        if intensity >= 25:
            return "wary"
        return "uneasy"
    if focus == "disgust":
        if intensity >= 75:
            return "repulsed"
        if intensity >= 50:
            return "disgusted"
        if intensity >= 25:
            return "grossed_out"
        return "put_off"
    return "neutral"


def derive_response_guidance(state: EmotionState) -> ResponseGuidance:
    """Select the highest emotion and map its intensity to a tone string."""
    focus, intensity = _focused_emotion(state)
    profile = TONE_PROFILES.get(_focused_tone(focus, intensity), {})
    return ResponseGuidance(
        focus=focus,
        intensity=intensity,
        tone=_focused_tone(focus, intensity),
        behavior=profile.get("behavior"),
    )
