"""Standalone Hermes affect prototype."""

from .decay import (
    DEFAULT_HALF_LIVES_HOURS,
    decay_state,
    load_half_lives,
)
from .events import EventRules, UnknownEventError
from .persistence import StateFileError, load_state, save_state
from .response import ResponseGuidance, derive_response_guidance
from .runtime import AffectRuntime, RuntimeSnapshot
from .state import EMOTIONS, EmotionState

__all__ = [
    "EMOTIONS",
    "EmotionState",
    "EventRules",
    "UnknownEventError",
    "DEFAULT_HALF_LIVES_HOURS",
    "decay_state",
    "load_half_lives",
    "StateFileError",
    "load_state",
    "save_state",
    "ResponseGuidance",
    "derive_response_guidance",
    "AffectRuntime",
    "RuntimeSnapshot",
]
