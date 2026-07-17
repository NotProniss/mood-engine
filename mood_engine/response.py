"""Response guidance derived from expression signals."""

from __future__ import annotations

from dataclasses import dataclass

from .behavior import BehaviorSignals


@dataclass(frozen=True)
class ResponseGuidance:
    """Inspectable style guidance for a future response generator."""

    tone: str
    energy: str
    stance: str
    initiative: str
    reflection: str

    def to_dict(self) -> dict[str, str]:
        return {
            "tone": self.tone,
            "energy": self.energy,
            "stance": self.stance,
            "initiative": self.initiative,
            "reflection": self.reflection,
        }


def _three_way(value: float, positive: str, negative: str, neutral: str) -> str:
    if value >= 20:
        return positive
    if value <= -20:
        return negative
    return neutral


def derive_response_guidance(signals: BehaviorSignals) -> ResponseGuidance:
    """Convert signed expression signals into coarse response guidance labels."""
    return ResponseGuidance(
        tone=_three_way(signals.warmth, "warm", "reserved", "neutral"),
        energy=_three_way(signals.energy, "lively", "quiet", "steady"),
        stance="careful" if signals.caution >= 20 else "open",
        initiative=_three_way(signals.initiative, "proactive", "responsive", "balanced"),
        reflection="reflective" if signals.reflection >= 20 else "low",
    )
