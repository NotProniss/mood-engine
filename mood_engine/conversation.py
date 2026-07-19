"""Simple conversation-context classification for completed turns."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path


SIGNALS_PATH = Path(__file__).parents[1] / "config" / "conversation_signals.json"

CONVERSATION_TYPES = (
    "casual",
    "pleasant",
    "funny",
    "awkward",
    "unpleasant",
    "offensive",
    "hurtful",
)

with SIGNALS_PATH.open(encoding="utf-8") as file:
    CONVERSATION_SIGNALS = json.load(file)


@dataclass(frozen=True)
class ConversationClassification:
    """The classified context for one completed message round."""

    conversation_type: str
    confidence: float
    event_name: str | None = None

    @property
    def is_casual(self) -> bool:
        return self.conversation_type == "casual"


def classify_round(
    user_message: str | None,
    assistant_response: str | None = None,
) -> ConversationClassification:
    """Classify one round conservatively; unmatched rounds remain casual.

    The user's wording is the signal source. The assistant response is accepted
    for future classifier expansion but is intentionally not interpreted yet,
    so Lilly's own wording cannot manufacture a mood event.
    """
    del assistant_response
    if not user_message:
        return ConversationClassification("casual", 1.0)

    normalized = re.sub(r"\s+", " ", user_message.casefold()).strip()
    for conversation_type, signal in CONVERSATION_SIGNALS.items():
        if any(re.search(pattern, normalized) for pattern in signal["patterns"]):
            return ConversationClassification(
                conversation_type=conversation_type,
                confidence=float(signal["confidence"]),
                event_name=signal["event"],
            )
    return ConversationClassification("casual", 0.9)
