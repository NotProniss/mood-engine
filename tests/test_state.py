import json
import unittest

from mood_engine.state import EmotionState


class EmotionStateTests(unittest.TestCase):
    def test_values_are_clamped_to_zero_and_one_hundred(self):
        state = EmotionState(joy=125, sadness=-10)

        self.assertEqual(state.joy, 100)
        self.assertEqual(state.sadness, 0)

    def test_state_round_trips_through_json(self):
        original = EmotionState(joy=12, sadness=34, anger=56, fear=78, disgust=90)

        restored = EmotionState.from_json(original.to_json())

        self.assertEqual(restored, original)

    def test_json_is_an_object_with_all_five_emotions(self):
        state = EmotionState()

        payload = json.loads(state.to_json())

        self.assertEqual(
            set(payload),
            {"joy", "sadness", "anger", "fear", "disgust"},
        )


if __name__ == "__main__":
    unittest.main()
