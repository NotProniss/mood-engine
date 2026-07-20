"""In-memory coordinator for affect state and focused response guidance."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import PLUGIN_CONFIG, config_path
from .decay import DEFAULT_BASELINES, DEFAULT_HALF_LIVES_HOURS, decay_state
from .events import EventRules
from .persistence import load_state as load_persisted_state
from .persistence import save_state as save_persisted_state
from .response import FocusedResponse, derive_focused_response
from .state import EmotionState


DEFAULT_RULES_PATH = config_path(PLUGIN_CONFIG["paths"]["emotion_rules"])


@dataclass(frozen=True)
class RuntimeSnapshot:
    """The complete inspectable output of one runtime evaluation."""

    state: EmotionState
    focused: FocusedResponse

    def to_dict(self) -> dict[str, dict]:
        return {"emotions": self.state.to_dict(), "focused": self.focused.to_dict()}


class AffectRuntime:
    """Coordinate state updates and focused guidance without external side effects."""

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
        state, updated_at = load_persisted_state(path, now=now, half_lives_hours=half_lives_hours, baselines=baselines)
        return cls(state=state, event_rules=event_rules, half_lives_hours=half_lives_hours, baselines=baselines, updated_at=updated_at)

    def save_state(self, path: str | Path, *, updated_at: datetime | None = None) -> None:
        timestamp = updated_at or self.updated_at or datetime.now(timezone.utc)
        save_persisted_state(path, self.state, timestamp)
        self.updated_at = timestamp

    def inspect(self) -> RuntimeSnapshot:
        return RuntimeSnapshot(self.state, derive_focused_response(self.state))

    def advance_time(self, *, elapsed_hours: float) -> RuntimeSnapshot:
        self.state = decay_state(self.state, elapsed_hours, half_lives_hours=self.half_lives_hours, baselines=self.baselines)
        if self.updated_at is not None:
            self.updated_at += timedelta(hours=elapsed_hours)
        return self.inspect()

    def process_event(
        self,
        event_name: str,
        *,
        elapsed_hours: float = 0,
        confidence: float = 1.0,
        intensity: float = 0.0,
    ) -> RuntimeSnapshot:
        self.state = decay_state(self.state, elapsed_hours, half_lives_hours=self.half_lives_hours, baselines=self.baselines)
        self.state = self.event_rules.apply(
            self.state,
            event_name,
            confidence=confidence,
            intensity=intensity,
        )
        if self.updated_at is not None:
            self.updated_at += timedelta(hours=elapsed_hours)
        return self.inspect()
