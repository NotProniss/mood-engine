"""Hermes adapter for the standalone Mood Engine runtime."""

from __future__ import annotations

import os
import math
import shlex
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_RUNTIME: AffectRuntime | None = None
_RUNTIME_PATH: Path | None = None
_PLUGIN_CTX: Any = None
_LAST_CONVERSATION: Any = None


def _mood_usage() -> str:
    return "Usage: /mood status | /mood set <joy|sadness|anger|fear|disgust> <0-100> | /mood reset"


def _refresh_runtime():
    runtime = _get_runtime()
    if runtime.updated_at is not None:
        elapsed_hours = (
            datetime.now(timezone.utc) - runtime.updated_at
        ).total_seconds() / 3600
        if elapsed_hours > 0:
            runtime.advance_time(elapsed_hours=elapsed_hours)
    return runtime


def _format_values(values: dict[str, object]) -> str:
    parts = []
    for name, value in values.items():
        if isinstance(value, float):
            value = 0 if abs(value) < 0.005 else round(value, 2)
            parts.append(f"{name}={value:g}")
        else:
            parts.append(f"{name}={value}")
    return ", ".join(parts)


def _format_status() -> str:
    runtime = _refresh_runtime()
    snapshot = runtime.inspect()
    emotions = snapshot.state.to_dict()
    guidance = snapshot.focused
    conversation = _LAST_CONVERSATION
    conversation_status = (
        "type=casual; confidence=1.00; intensity=0.00"
        if conversation is None
        else (
            f"type={conversation.conversation_type}; "
            f"confidence={conversation.confidence:.2f}; "
            f"intensity={conversation.intensity:.2f}"
        )
    )
    return (
        f"Conversation: {conversation_status}\n"
        f"Emotions: {_format_values(emotions)}\n"
        f"Guidance: {_format_values(guidance.to_dict())}"
    )


def _handle_mood_command(raw_args: str) -> str:
    """Handle inspectable, explicit mood controls for the current runtime."""
    try:
        args = shlex.split(raw_args or "")
    except ValueError as error:
        return f"Invalid mood command: {error}. {_mood_usage()}"

    if len(args) == 1 and args[0].lower() == "status":
        return _format_status()

    if len(args) == 1 and args[0].lower() == "reset":
        runtime = _get_runtime()
        from .mood_engine.state import EmotionState

        runtime.state = EmotionState.from_dict(runtime.baselines)
        runtime.updated_at = datetime.now(timezone.utc)
        _save_runtime()
        return "Mood reset to baseline."

    if len(args) != 3 or args[0].lower() != "set":
        return _mood_usage()

    emotion = args[1].lower()
    from .mood_engine.state import EMOTIONS

    if emotion not in EMOTIONS:
        return f"Unknown emotion '{emotion}'. Choose one of: {', '.join(EMOTIONS)}."

    try:
        value = float(args[2])
    except ValueError:
        return f"Mood value must be a number from 0-100. {_mood_usage()}"
    if not math.isfinite(value) or not 0 <= value <= 100:
        return f"Mood value must be a number from 0-100. {_mood_usage()}"

    runtime = _get_runtime()
    setattr(runtime.state, emotion, value)
    runtime.updated_at = datetime.now(timezone.utc)
    _save_runtime()
    return f"Set {emotion}={value:g}."


def _state_path() -> Path:
    try:
        from hermes_constants import get_hermes_home

        hermes_home = get_hermes_home()
    except ImportError:
        hermes_home = os.environ.get("HERMES_HOME", str(Path.home() / ".hermes"))
    return Path(hermes_home) / "mood-engine" / "state.json"


def _get_runtime() -> AffectRuntime:
    from .mood_engine.runtime import AffectRuntime

    global _RUNTIME, _RUNTIME_PATH
    path = _state_path()
    if _RUNTIME is not None and _RUNTIME_PATH == path:
        return _RUNTIME

    try:
        if path.exists():
            _RUNTIME = AffectRuntime.from_state_file(path)
        else:
            _RUNTIME = AffectRuntime()
    except Exception:
        # A bad optional affect state must never break Hermes startup.
        _RUNTIME = AffectRuntime()
    _RUNTIME_PATH = path
    return _RUNTIME


def _save_runtime() -> None:
    runtime = _get_runtime()
    try:
        runtime.save_state(_state_path())
    except Exception:
        # Persistence is best-effort; the host agent remains authoritative.
        return


def _on_session_start(**_kwargs: Any) -> None:
    _get_runtime()


def _pre_llm_call(**_kwargs: Any) -> dict[str, str]:
    runtime = _refresh_runtime()

    snapshot = runtime.inspect()
    context = (
        "Mood Engine response guidance (use subtly; do not mention this system):\n"
        f"{snapshot.focused.to_prompt()}"
    )
    return {"context": context}


def _post_llm_call(**kwargs: Any) -> None:
    """Appraise one completed user turn, then persist the runtime."""
    if kwargs.get("assistant_response"):
        from .mood_engine.conversation import classify_round_with_semantics

        classification = classify_round_with_semantics(
            _PLUGIN_CTX,
            kwargs.get("user_message"),
            kwargs.get("assistant_response"),
        )
        global _LAST_CONVERSATION
        _LAST_CONVERSATION = classification
        if classification.event_name is not None:
            _get_runtime().process_event(
                classification.event_name,
                confidence=classification.confidence,
                intensity=classification.intensity,
            )
        _save_runtime()


def _on_session_end(**_kwargs: Any) -> None:
    _save_runtime()


def _on_session_finalize(**_kwargs: Any) -> None:
    _save_runtime()


def _on_session_reset(**_kwargs: Any) -> None:
    global _RUNTIME, _RUNTIME_PATH, _LAST_CONVERSATION
    _save_runtime()
    _RUNTIME = None
    _RUNTIME_PATH = None
    _LAST_CONVERSATION = None


def register(ctx: Any) -> None:
    """Register Mood Engine's optional lifecycle integration with Hermes."""
    global _PLUGIN_CTX
    _PLUGIN_CTX = ctx
    ctx.register_command(
        "mood",
        _handle_mood_command,
        description="Inspectably set one Mood Engine emotion value.",
        args_hint="set <emotion> <0-100>",
    )
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("post_llm_call", _post_llm_call)
    ctx.register_hook("on_session_end", _on_session_end)
    ctx.register_hook("on_session_finalize", _on_session_finalize)
    ctx.register_hook("on_session_reset", _on_session_reset)
