"""In-memory coordinator for emotion state and response guidance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .decay import DEFAULT_BASELINES, DEFAULT_HALF_LIVES_HOURS, decay_state
from .events import EventContext, EventRules
from .persistence import load_state as load_persisted_state
from .persistence import save_state as save_persisted_state
from .response import ResponseGuidance, derive_response_guidance
from .state import EmotionState


DEFAULT_RULES_PATH = Path(__file__).parents[1] / "config" / "emotion_rules.json"


@dataclass(frozen=True)
class RuntimeSnapshot:
    """The complete inspectable output of one runtime evaluation."""

    state: EmotionState
    guidance: ResponseGuidance

    def to_dict(self) -> dict[str, dict]:
        return {
            "emotions": self.state.to_dict(),
            "guidance": self.guidance.to_dict(),
        }


class AffectRuntime:
    """Coordinate state updates and derived output without external side effects."""

    def __init__(
        self,
        state: EmotionState | None = None,
        event_rules: EventRules | None = None,
        half_lives_hours: dict[str, float] | None = None,
        baselines: dict[str, float] | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        self.state = state or EmotionState()
        self.event_rules = event_rules or EventRules.from_json_file(DEFAULT_RULES_PATH)
        self.half_lives_hours = half_lives_hours or DEFAULT_HALF_LIVES_HOURS
        self.baselines = baselines or DEFAULT_BASELINES
        self.updated_at = updated_at

    @classmethod
    def from_state_file(
        cls,
        path: str | Path,
        *,
        now: datetime | None = None,
        event_rules: EventRules | None = None,
        half_lives_hours: dict[str, float] | None = None,
        baselines: dict[str, float] | None = None,
    ) -> "AffectRuntime":
        """Load persisted state, applying elapsed decay exactly once."""
        state, updated_at = load_persisted_state(
            path,
            now=now,
            half_lives_hours=half_lives_hours,
            baselines=baselines,
        )
        return cls(
            state=state,
            event_rules=event_rules,
            half_lives_hours=half_lives_hours,
            baselines=baselines,
            updated_at=updated_at,
        )

    def save_state(
        self,
        path: str | Path,
        *,
        updated_at: datetime | None = None,
    ) -> None:
        """Persist emotion state and timestamp, excluding derived outputs."""
        timestamp = updated_at or self.updated_at or datetime.now(timezone.utc)
        save_persisted_state(path, self.state, timestamp)
        self.updated_at = timestamp

    def inspect(self) -> RuntimeSnapshot:
        """Return current state plus focused response guidance."""
        guidance = derive_response_guidance(self.state)
        return RuntimeSnapshot(self.state, guidance)

    def advance_time(self, *, elapsed_hours: float) -> RuntimeSnapshot:
        """Apply decay without creating an event."""
        self.state = decay_state(
            self.state,
            elapsed_hours,
            half_lives_hours=self.half_lives_hours,
            baselines=self.baselines,
        )
        if self.updated_at is not None:
            self.updated_at += timedelta(hours=elapsed_hours)
        return self.inspect()

    def process_event(
        self,
        event_name: str,
        *,
        elapsed_hours: float = 0,
        context: EventContext | None = None,
    ) -> RuntimeSnapshot:
        """Apply decay, process one event, and return the resulting snapshot."""
        self.state = decay_state(
            self.state,
            elapsed_hours,
            half_lives_hours=self.half_lives_hours,
            baselines=self.baselines,
        )
        self.state = self.event_rules.apply(self.state, event_name, context)
        if self.updated_at is not None:
            self.updated_at += timedelta(hours=elapsed_hours)
        return self.inspect()
