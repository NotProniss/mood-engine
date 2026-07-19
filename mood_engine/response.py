"""Minimal focused response guidance derived from emotion state."""

from __future__ import annotations

from dataclasses import dataclass

from .state import EMOTIONS, EmotionState


_TONE_BANDS = {
    "joy": ((24, "content"), (49, "happy"), (74, "excited"), (100, "ecstatic")),
    "sadness": ((24, "downcast"), (49, "sad"), (74, "heavy"), (100, "sorrowful")),
    "anger": ((24, "annoyed"), (49, "irritated"), (74, "aggressive"), (100, "scathing")),
    "fear": ((24, "uneasy"), (49, "wary"), (74, "anxious"), (100, "horrified")),
    "disgust": ((24, "put_off"), (49, "grossed_out"), (74, "disgusted"), (100, "repulsed")),
}

_BEHAVIOR_PROFILES = {
    "sorrowful": "Speak gently and reflectively. Avoid cheerfulness, teasing, and excessive enthusiasm.",
}


@dataclass(frozen=True)
class FocusedResponse:
    """The smallest inspectable response-style projection of current affect."""

    focus: str
    intensity: float
    tone: str
    behavior: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "focus": self.focus,
            "intensity": self.intensity,
            "tone": self.tone,
            "behavior": self.behavior,
        }

    def to_prompt(self) -> str:
        prompt = f"focus={self.focus}; tone={self.tone}"
        if self.behavior:
            prompt += f"; behavior={self.behavior}"
        return prompt


def _tone_for(focus: str, intensity: float) -> str:
    for upper_bound, tone in _TONE_BANDS[focus]:
        if intensity <= upper_bound:
            return tone
    return _TONE_BANDS[focus][-1][1]


def derive_focused_response(state: EmotionState) -> FocusedResponse:
    """Select the highest raw emotion and map it to a bounded tone label."""
    focus = max(EMOTIONS, key=lambda emotion: getattr(state, emotion))
    intensity = getattr(state, focus)
    if intensity <= 0:
        return FocusedResponse("neutral", 0, "neutral")

    tone = _tone_for(focus, intensity)
    return FocusedResponse(focus, intensity, tone, _BEHAVIOR_PROFILES.get(tone))
