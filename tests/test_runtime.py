import unittest
from pathlib import Path

from mood_engine.events import EventContext, EventRules
from mood_engine.response import ResponseGuidance
from mood_engine.runtime import AffectRuntime, RuntimeSnapshot
from mood_engine.state import EmotionState


RULES_PATH = Path(__file__).parents[1] / "config" / "emotion_rules.json"


class AffectRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = EventRules.from_json_file(RULES_PATH)

    def test_inspect_returns_the_full_derived_pipeline(self):
        runtime = AffectRuntime(state=EmotionState(joy=25), event_rules=self.rules)

        snapshot = runtime.inspect()

        self.assertIsInstance(snapshot, RuntimeSnapshot)
        self.assertIsInstance(snapshot.state, EmotionState)
        self.assertIsInstance(snapshot.guidance, ResponseGuidance)
        self.assertEqual(snapshot.state.joy, 25)

    def test_advance_time_applies_decay_without_an_event(self):
        runtime = AffectRuntime(
            state=EmotionState(joy=80),
            event_rules=self.rules,
        )

        snapshot = runtime.advance_time(elapsed_hours=6)

        self.assertAlmostEqual(snapshot.state.joy, 40.0)

    def test_process_event_updates_state_and_derived_outputs(self):
        runtime = AffectRuntime(event_rules=self.rules)

        snapshot = runtime.process_event("warm_conversation")

        self.assertEqual(snapshot.state.joy, 1)
        self.assertEqual(snapshot.state.sadness, 0)
        self.assertEqual(snapshot.guidance.focus, "joy")
        self.assertEqual(snapshot.guidance.intensity, 1)
        self.assertEqual(snapshot.guidance.tone, "content")

    def test_process_event_applies_decay_before_event(self):
        runtime = AffectRuntime(
            state=EmotionState(joy=80),
            event_rules=self.rules,
        )

        snapshot = runtime.process_event("quiet_companionship", elapsed_hours=6)

        self.assertAlmostEqual(snapshot.state.joy, 43.0)
        self.assertEqual(snapshot.state.sadness, 0)

    def test_context_reaches_event_appraisal(self):
        runtime = AffectRuntime(event_rules=self.rules)

        snapshot = runtime.process_event(
            "long_absence",
            context=EventContext(absence_explained=True),
        )

        self.assertEqual(snapshot.state.sadness, 1)


if __name__ == "__main__":
    unittest.main()
