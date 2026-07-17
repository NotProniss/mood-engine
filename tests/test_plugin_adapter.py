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

    def register_hook(self, name, callback):
        self.hooks[name] = callback


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


def test_pre_llm_hook_returns_compact_guidance(monkeypatch, tmp_path):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))
    plugin = load_plugin()
    context = FakeContext()
    plugin.register(context)

    result = context.hooks["pre_llm_call"](session_id="test-session")

    assert isinstance(result, dict)
    assert "context" in result
    assert "Mood Engine" in result["context"]
    assert "warmth" in result["context"]


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
    assert '"joy": 8' in state_path.read_text(encoding="utf-8")
