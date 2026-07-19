import unittest
from pathlib import Path

from mood_engine.events import EventRules
from mood_engine.response import FocusedResponse
from mood_engine.runtime import AffectRuntime, RuntimeSnapshot
from mood_engine.state import EmotionState


RULES_PATH = Path(__file__).parents[1] / "config" / "emotion_rules.json"


class AffectRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = EventRules.from_json_file(RULES_PATH)

    def test_inspect_returns_state_and_focused_response(self):
        runtime = AffectRuntime(state=EmotionState(joy=25), event_rules=self.rules)
        snapshot = runtime.inspect()
        self.assertIsInstance(snapshot, RuntimeSnapshot)
        self.assertIsInstance(snapshot.state, EmotionState)
        self.assertIsInstance(snapshot.focused, FocusedResponse)
        self.assertEqual(snapshot.focused.to_prompt(), "focus=joy; tone=happy")

    def test_advance_time_applies_decay_without_an_event(self):
        runtime = AffectRuntime(state=EmotionState(joy=80), event_rules=self.rules)
        snapshot = runtime.advance_time(elapsed_hours=6)
        self.assertAlmostEqual(snapshot.state.joy, 40.0)

    def test_process_event_updates_state_and_focus(self):
        runtime = AffectRuntime(event_rules=self.rules)
        snapshot = runtime.process_event("pleasant_conversation")
        self.assertEqual(snapshot.state.joy, 1)
        self.assertEqual(snapshot.focused.to_prompt(), "focus=joy; tone=content")

    def test_process_event_applies_decay_before_event(self):
        runtime = AffectRuntime(state=EmotionState(joy=80), event_rules=self.rules)
        snapshot = runtime.process_event("funny_conversation", elapsed_hours=6)
        self.assertAlmostEqual(snapshot.state.joy, 42.0)

    def test_process_event_updates_sadness_focus(self):
        runtime = AffectRuntime(event_rules=self.rules)
        snapshot = runtime.process_event("hurtful_conversation")
        self.assertEqual(snapshot.state.sadness, 1)
        self.assertEqual(snapshot.focused.to_prompt(), "focus=sadness; tone=downcast")


if __name__ == "__main__":
    unittest.main()
