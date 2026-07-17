"""Persistence for the Hermes affect runtime state."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .decay import DEFAULT_HALF_LIVES_HOURS, decay_state
from .state import EmotionState


STATE_VERSION = 1


class StateFileError(ValueError):
    """Raised when a runtime state file cannot be safely loaded."""


def _require_aware_utc(value: datetime, name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise StateFileError(f"{name} must include a timezone")
    return value.astimezone(timezone.utc)


def save_state(path: str | Path, state: EmotionState, updated_at: datetime) -> None:
    """Write a versioned, inspectable runtime state file."""
    timestamp = _require_aware_utc(updated_at, "updated_at")
    payload = {
        "version": STATE_VERSION,
        "updated_at": timestamp.isoformat(),
        "emotions": state.to_dict(),
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def load_state(
    path: str | Path,
    now: datetime | None = None,
    half_lives_hours: dict[str, float] | None = None,
    baselines: dict[str, float] | None = None,
) -> tuple[EmotionState, datetime]:
    """Load state, apply elapsed decay, and return the refreshed timestamp."""
    target = Path(path)
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise StateFileError("State file must contain an object")
        if payload.get("version") != STATE_VERSION:
            raise StateFileError(f"Unsupported state file version: {payload.get('version')}")

        updated_at = datetime.fromisoformat(payload["updated_at"])
        updated_at = _require_aware_utc(updated_at, "updated_at")
        state = EmotionState.from_dict(payload["emotions"])
    except StateFileError:
        raise
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        raise StateFileError(f"Could not load state file {target}: {error}") from error

    current_time = _require_aware_utc(now or datetime.now(timezone.utc), "now")
    if current_time < updated_at:
        raise StateFileError("State timestamp is in the future")

    elapsed_hours = (current_time - updated_at).total_seconds() / 3600
    refreshed = decay_state(
        state,
        elapsed_hours,
        half_lives_hours or DEFAULT_HALF_LIVES_HOURS,
        baselines=baselines,
    )
    return refreshed, current_time
