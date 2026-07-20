import unittest
from pathlib import Path

from mood_engine.events import EventRules, UnknownEventError
from mood_engine.state import EmotionState


RULES_PATH = Path(__file__).parents[1] / "config" / "emotion_rules.json"


class EventRulesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = EventRules.from_json_file(RULES_PATH)

    def test_conversation_events_have_one_primary_emotion_each(self):
        cases = (
            ("pleasant", "joy"),
            ("funny", "joy"),
            ("awkward", "fear"),
            ("unpleasant", "disgust"),
            ("offensive", "anger"),
            ("hurtful", "sadness"),
        )
        for event_name, emotion in cases:
            with self.subTest(event_name=event_name):
                updated = self.rules.apply(EmotionState(), event_name)
                self.assertEqual(getattr(updated, emotion), 1 if event_name != "funny" else 2)
                other_values = updated.to_dict()
                other_values.pop(emotion)
                self.assertTrue(all(value == 0 for value in other_values.values()))

    def test_casual_conversation_is_not_an_event(self):
        with self.assertRaises(UnknownEventError):
            self.rules.apply(EmotionState(), "casual_conversation")

    def test_unknown_event_raises_clear_error(self):
        with self.assertRaises(UnknownEventError):
            self.rules.apply(EmotionState(), "made_up_event")

    def test_repeated_events_remain_bounded(self):
        state = EmotionState()
        for _ in range(60):
            state = self.rules.apply(state, "funny")
        self.assertEqual(state.joy, 100)


if __name__ == "__main__":
    unittest.main()
