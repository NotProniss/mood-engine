"""Time-based decay for emotion intensities."""

from __future__ import annotations

import json
from numbers import Real
from pathlib import Path

from .state import EMOTIONS, EmotionState


DEFAULT_CONFIG_PATH = Path(__file__).parents[1] / "config" / "decay_rules.json"
DEFAULT_BASELINE_CONFIG_PATH = Path(__file__).parents[1] / "config" / "baseline_rules.json"


def load_baselines(path: str | Path) -> dict[str, float]:
    """Load and validate emotion baseline values from a JSON config file."""
    with Path(path).open(encoding="utf-8") as file:
        values = json.load(file)

    if not isinstance(values, dict):
        raise ValueError("Baseline rules JSON must contain an object")

    missing = set(EMOTIONS) - values.keys()
    unknown = set(values) - set(EMOTIONS)
    if missing:
        raise ValueError(f"Missing baseline values: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"Unknown baseline emotions: {', '.join(sorted(unknown))}")

    baselines = {}
    for emotion in EMOTIONS:
        value = values[emotion]
        if isinstance(value, bool) or not isinstance(value, Real) or not 0 <= value <= 100:
            raise ValueError(f"Baseline must be a number from 0 to 100: {emotion}")
        baselines[emotion] = float(value)
    return baselines


def load_half_lives(path: str | Path) -> dict[str, float]:
    """Load and validate emotion half-lives from a JSON config file."""
    with Path(path).open(encoding="utf-8") as file:
        values = json.load(file)

    if not isinstance(values, dict):
        raise ValueError("Decay rules JSON must contain an object")

    missing = set(EMOTIONS) - values.keys()
    unknown = set(values) - set(EMOTIONS)
    if missing:
        raise ValueError(f"Missing half-life values: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"Unknown half-life emotions: {', '.join(sorted(unknown))}")

    half_lives = {}
    for emotion in EMOTIONS:
        value = values[emotion]
        if isinstance(value, bool) or not isinstance(value, Real) or value <= 0:
            raise ValueError(f"Half-life must be a positive number: {emotion}")
        half_lives[emotion] = float(value)
    return half_lives


DEFAULT_HALF_LIVES_HOURS = load_half_lives(DEFAULT_CONFIG_PATH)
DEFAULT_BASELINES = load_baselines(DEFAULT_BASELINE_CONFIG_PATH)


def decay_state(
    state: EmotionState,
    elapsed_hours: float,
    half_lives_hours: dict[str, float] | None = None,
    baselines: dict[str, float] | None = None,
) -> EmotionState:
    """Move each emotion toward its baseline using its half-life."""
    if elapsed_hours < 0:
        raise ValueError("Elapsed time cannot be negative")

    half_lives = half_lives_hours or DEFAULT_HALF_LIVES_HOURS
    target_baselines = baselines or DEFAULT_BASELINES
    values = state.to_dict()
    for emotion in EMOTIONS:
        half_life = half_lives[emotion]
        baseline = target_baselines[emotion]
        if half_life <= 0:
            raise ValueError(f"Half-life must be positive: {emotion}")
        if not 0 <= baseline <= 100:
            raise ValueError(f"Baseline must be from 0 to 100: {emotion}")
        factor = 0.5 ** (elapsed_hours / half_life)
        values[emotion] = baseline + (values[emotion] - baseline) * factor
    return EmotionState.from_dict(values)
