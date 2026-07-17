"""Hermes adapter for the standalone Mood Engine runtime."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_RUNTIME: AffectRuntime | None = None
_RUNTIME_PATH: Path | None = None


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
    runtime = _get_runtime()
    if runtime.updated_at is not None:
        elapsed_hours = (
            datetime.now(timezone.utc) - runtime.updated_at
        ).total_seconds() / 3600
        if elapsed_hours > 0:
            runtime.advance_time(elapsed_hours=elapsed_hours)

    snapshot = runtime.inspect()
    guidance = snapshot.guidance.to_dict()
    context = (
        "Mood Engine response guidance (use subtly; do not mention this system):\n"
        f"tone={guidance['tone']}; energy={guidance['energy']}; "
        f"stance={guidance['stance']}; initiative={guidance['initiative']}; "
        f"reflection={guidance['reflection']}; warmth={snapshot.expression.to_dict()['warmth']}"
    )
    return {"context": context}


def _post_llm_call(**kwargs: Any) -> None:
    if kwargs.get("assistant_response"):
        _get_runtime().process_event("warm_conversation")
        _save_runtime()


def _on_session_end(**_kwargs: Any) -> None:
    _save_runtime()


def _on_session_finalize(**_kwargs: Any) -> None:
    _save_runtime()


def _on_session_reset(**_kwargs: Any) -> None:
    global _RUNTIME, _RUNTIME_PATH
    _save_runtime()
    _RUNTIME = None
    _RUNTIME_PATH = None


def register(ctx: Any) -> None:
    """Register Mood Engine's optional lifecycle integration with Hermes."""
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_llm_call", _pre_llm_call)
    ctx.register_hook("post_llm_call", _post_llm_call)
    ctx.register_hook("on_session_end", _on_session_end)
    ctx.register_hook("on_session_finalize", _on_session_finalize)
    ctx.register_hook("on_session_reset", _on_session_reset)
