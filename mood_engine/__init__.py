"""Standalone Hermes affect prototype."""

from .decay import (
    DEFAULT_HALF_LIVES_HOURS,
    decay_state,
    load_half_lives,
)
from .events import EventRules, UnknownEventError
from .conversation import ConversationClassification, classify_round, classify_round_with_semantics
from .persistence import StateFileError, load_state, save_state
from .response import FocusedResponse, derive_focused_response
from .runtime import AffectRuntime, RuntimeSnapshot
from .state import EMOTIONS, EmotionState

__all__ = [
    "EMOTIONS",
    "EmotionState",
    "EventRules",
    "UnknownEventError",
    "ConversationClassification",
    "classify_round",
    "DEFAULT_HALF_LIVES_HOURS",
    "decay_state",
    "load_half_lives",
    "StateFileError",
    "load_state",
    "save_state",
    "FocusedResponse",
    "derive_focused_response",
    "AffectRuntime",
    "RuntimeSnapshot",
]
