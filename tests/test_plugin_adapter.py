import importlib.util
import sys
import types
from pathlib import Path


PROJECT_ROOT = Path(__file__).parents[1]
PLUGIN_PATH = PROJECT_ROOT / "__init__.py"


def load_plugin():
    package_name = "mood_engine_plugin_under_test"
    spec = importlib.util.spec_from_file_location(
        package_name,
        PLUGIN_PATH,
        submodule_search_locations=[str(PROJECT_ROOT)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[package_name] = module
    spec.loader.exec_module(module)
    return module


class FakeContext:
    def __init__(self):
        self.hooks = {}
        self.commands = {}

    def register_hook(self, name, callback):
        self.hooks[name] = callback

    def register_command(self, name, handler, **kwargs):
        self.commands[name] = (handler, kwargs)


def test_registers_runtime_lifecycle_hooks():
    plugin = load_plugin()
    context = FakeContext()

    plugin.register(context)

    assert set(context.hooks) == {
        "on_session_start",
        "pre_llm_call",
        "post_llm_call",
        "on_session_end",
        "on_session_finalize",
        "on_session_reset",
    }
    assert "mood" in context.commands


def test_pre_llm_hook_returns_compact_guidance(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    plugin = load_plugin()
    context = FakeContext()
    plugin.register(context)

    result = context.hooks["pre_llm_call"](session_id="test-session")

    assert isinstance(result, dict)
    assert "context" in result
    assert "Mood Engine" in result["context"]
    assert "tone=" in result["context"]
    assert "focus=" in result["context"]
    assert "intensity=" not in result["context"]
    assert "warmth" not in result["context"]


def test_post_llm_hook_records_and_persists_warm_interaction(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    plugin = load_plugin()
    context = FakeContext()
    plugin.register(context)

    context.hooks["post_llm_call"](
        session_id="test-session",
        user_message="hello",
        assistant_response="Hi there!",
    )

    state_path = tmp_path / ".hermes" / "mood-engine" / "state.json"
    assert state_path.exists()
    assert '"joy": 0' in state_path.read_text(encoding="utf-8")


def test_post_llm_hook_classifies_offensive(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    plugin = load_plugin()
    context = FakeContext()
    plugin.register(context)

    context.hooks["post_llm_call"](
        user_message="That was rude and insulting.",
        assistant_response="Understood.",
    )

    state = plugin._get_runtime().state
    assert state.anger == 1
    assert state.sadness == 0


def test_mood_status_reports_last_conversation_and_confidence(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    plugin = load_plugin()
    context = FakeContext()
    plugin.register(context)

    context.hooks["post_llm_call"](
        user_message="That was hilarious, haha.",
        assistant_response="Heh.",
    )

    result = context.commands["mood"][0]("status")

    assert "Conversation: type=funny; confidence=0.80; intensity=0.50" in result
    assert "Guidance: focus=joy" in result
    assert "intensity=2" in result


def test_mood_status_reports_emotions_and_guidance(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    plugin = load_plugin()
    context = FakeContext()
    plugin.register(context)

    handler = context.commands["mood"][0]
    handler("set anger 80")

    result = handler("status")

    assert "Emotions:" in result
    assert "anger=80" in result
    assert "focus=anger" in result
    assert "intensity=80" in result
    assert "tone=" in result
    assert "Guidance:" in result
    assert "tone=scathing" in result


def test_mood_set_updates_only_requested_emotion(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    plugin = load_plugin()
    context = FakeContext()
    plugin.register(context)

    result = context.commands["mood"][0]("set anger 100")

    assert "anger=100" in result
    assert plugin._get_runtime().state.anger == 100
    assert plugin._get_runtime().state.joy == 0


def test_mood_set_rejects_unknown_emotion(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    plugin = load_plugin()
    context = FakeContext()
    plugin.register(context)

    result = context.commands["mood"][0]("set calm 50")

    assert "Unknown emotion" in result


def test_mood_set_rejects_values_outside_range(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    plugin = load_plugin()
    context = FakeContext()
    plugin.register(context)

    result = context.commands["mood"][0]("set anger 101")

    assert "0-100" in result


def test_mood_reset_restores_configured_baselines(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    plugin = load_plugin()
    context = FakeContext()
    plugin.register(context)
    handler = context.commands["mood"][0]

    handler("set anger 100")
    result = handler("reset")

    assert result == "Mood reset to baseline."
    assert plugin._get_runtime().state.to_dict() == plugin._get_runtime().baselines
