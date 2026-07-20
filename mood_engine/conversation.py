"""Configurable conversation classification for completed turns."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CONFIG_DIR = Path(__file__).parents[1] / "config"
SIGNALS_PATH = CONFIG_DIR / "conversation_signals.json"
EMOTION_RULES_PATH = CONFIG_DIR / "emotion_rules.json"
CLASSIFIER_PATH = CONFIG_DIR / "conversation_classifier.json"

with SIGNALS_PATH.open(encoding="utf-8") as file:
    CONVERSATION_SIGNALS: dict[str, dict[str, Any]] = json.load(file)
with EMOTION_RULES_PATH.open(encoding="utf-8") as file:
    EMOTION_RULES: dict[str, dict[str, float]] = json.load(file)
with CLASSIFIER_PATH.open(encoding="utf-8") as file:
    CLASSIFIER_CONFIG: dict[str, Any] = json.load(file)

# emotion_rules.json is the source of truth for supported non-casual labels.
# Casual is the reserved neutral baseline and has no event rule.
CONVERSATION_TYPES = ("casual", *EMOTION_RULES.keys())


@dataclass(frozen=True)
class ConversationClassification:
    """The classified context for one completed message round."""

    conversation_type: str
    confidence: float
    intensity: float = 0.0
    event_name: str | None = None

    @property
    def is_casual(self) -> bool:
        return self.conversation_type == "casual"


def _rule_classify(user_message: str | None) -> ConversationClassification:
    """Classify with configured patterns; unmatched rounds remain casual."""
    if not user_message:
        return ConversationClassification("casual", 1.0)

    normalized = re.sub(r"\s+", " ", user_message.casefold()).strip()
    for conversation_type, signal in CONVERSATION_SIGNALS.items():
        if conversation_type not in EMOTION_RULES:
            continue
        if any(re.search(pattern, normalized) for pattern in signal["patterns"]):
            return ConversationClassification(
                conversation_type=conversation_type,
                confidence=float(signal.get("confidence", 0.8)),
                intensity=float(signal.get("intensity", 0.5)),
                event_name=conversation_type,
            )
    return ConversationClassification("casual", 0.9)


def _semantic_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "conversation_type": {
                "type": "string",
                "enum": list(CONVERSATION_TYPES),
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "intensity": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
            },
        },
        "required": ["conversation_type", "confidence", "intensity"],
        "additionalProperties": False,
    }


def _classification_from_payload(payload: Any) -> ConversationClassification | None:
    if not isinstance(payload, dict):
        return None
    label = payload.get("conversation_type")
    confidence = payload.get("confidence")
    intensity = payload.get("intensity")
    if label not in CONVERSATION_TYPES:
        return None
    if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        return None
    if not isinstance(intensity, (int, float)) or not 0 <= intensity <= 1:
        return None
    if confidence < float(CLASSIFIER_CONFIG.get("minimum_confidence", 0.7)):
        return None
    if label == "casual":
        return ConversationClassification(label, float(confidence), float(intensity))
    return ConversationClassification(
        conversation_type=label,
        confidence=float(confidence),
        intensity=float(intensity),
        event_name=label,
    )


def classify_semantic_round(ctx: Any, user_message: str | None) -> ConversationClassification | None:
    """Ask Hermes' active model for a strict, schema-validated classification.

    Returns None on missing LLM access, invalid output, low confidence, or any
    provider error. The caller should use the configured rule matcher then.
    """
    if not user_message or not getattr(ctx, "llm", None):
        return None
    labels = ", ".join(CONVERSATION_TYPES)
    instructions = (
        "Classify the user's message into exactly one conversation type. "
        f"Allowed types: {labels}. "
        "Casual is the neutral fallback. Use pleasant for appreciation, warmth, "
        "or enjoyment; funny for humor or laughter; awkward for embarrassment "
        "or social discomfort; unpleasant for irritation or disgust; offensive "
        "for rudeness or insults; hurtful for emotional pain, rejection, or "
        "dismissal. Return only the requested structured fields. Do not infer "
        "a type when the message is ambiguous."
    )
    try:
        result = ctx.llm.complete_structured(
            instructions=instructions,
            input=[{"type": "text", "text": user_message}],
            json_schema=_semantic_schema(),
            purpose="mood-engine.conversation-classifier",
            temperature=0.0,
            max_tokens=int(CLASSIFIER_CONFIG.get("max_tokens", 96)),
        )
    except Exception:
        return None
    return _classification_from_payload(getattr(result, "parsed", None))


def classify_round_with_semantics(
    ctx: Any,
    user_message: str | None,
    assistant_response: str | None = None,
) -> ConversationClassification:
    """Prefer semantic analysis when configured, otherwise use rule fallback."""
    del assistant_response
    if CLASSIFIER_CONFIG.get("mode", "rules") == "semantic":
        result = classify_semantic_round(ctx, user_message)
        if result is not None:
            return result
    return _rule_classify(user_message)


def classify_round(user_message: str | None, assistant_response: str | None = None) -> ConversationClassification:
    """Deterministic fallback used by tests and when semantic analysis fails."""
    del assistant_response
    return _rule_classify(user_message)
