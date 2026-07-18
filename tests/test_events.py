import unittest
from pathlib import Path

from mood_engine.events import EventContext, EventRules, UnknownEventError
from mood_engine.state import EmotionState


RULES_PATH = Path(__file__).parents[1] / "config" / "emotion_rules.json"


class EventRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = EventRules.from_json_file(RULES_PATH)

    def test_warm_conversation_is_a_small_nudge(self):
        state = EmotionState(sadness=10)

        updated = self.rules.apply(state, "warm_conversation")

        self.assertEqual(updated.joy, 1)
        self.assertEqual(updated.sadness, 9)

    def test_unknown_event_raises_clear_error(self):
        with self.assertRaises(UnknownEventError):
            self.rules.apply(EmotionState(), "made_up_event")

    def test_explained_absence_reduces_sadness_appraisal(self):
        state = EmotionState()

        updated = self.rules.apply(
            state,
            "long_absence",
            EventContext(absence_explained=True),
        )

        self.assertEqual(updated.sadness, 1)

    def test_quiet_companionship_gently_improves_state(self):
        updated = self.rules.apply(EmotionState(sadness=10), "quiet_companionship")

        self.assertEqual(updated.joy, 3)
        self.assertEqual(updated.sadness, 9)

    def test_repair_after_conflict_reduces_negative_emotions(self):
        updated = self.rules.apply(
            EmotionState(anger=8, sadness=6),
            "repair_after_conflict",
        )

        self.assertEqual(updated.joy, 5)
        self.assertEqual(updated.anger, 4)
        self.assertEqual(updated.sadness, 4)

    def test_return_after_absence_reduces_absence_sadness(self):
        updated = self.rules.apply(
            EmotionState(sadness=10, fear=3),
            "return_after_absence",
        )

        self.assertEqual(updated.joy, 6)
        self.assertEqual(updated.sadness, 7)
        self.assertEqual(updated.fear, 2)

    def test_repeated_events_remain_bounded(self):
        state = EmotionState()

        for _ in range(30):
            state = self.rules.apply(state, "interesting_discovery")

        self.assertEqual(state.joy, 100)


if __name__ == "__main__":
    unittest.main()
