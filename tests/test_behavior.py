import unittest

from mood_engine.behavior import BehaviorSignals, derive_behavior_signals
from mood_engine.state import EmotionState


class BehaviorSignalTests(unittest.TestCase):
    def test_baseline_state_produces_the_proposed_signals(self):
        signals = derive_behavior_signals(
            EmotionState(joy=25, sadness=5, anger=2, fear=3, disgust=1)
        )

        self.assertEqual(
            signals.to_dict(),
            {
                "warmth": 17,
                "energy": 17,
                "caution": 6,
                "initiative": 15,
                "reflection": 8,
            },
        )

    def test_signals_are_bounded_between_negative_and_positive_100(self):
        for state in (EmotionState(), EmotionState(joy=100, sadness=100, anger=100, fear=100, disgust=100)):
            signals = derive_behavior_signals(state)
            for value in signals.to_dict().values():
                self.assertGreaterEqual(value, -100)
                self.assertLessEqual(value, 100)

    def test_emotions_contribute_directly_to_output_signals(self):
        signals = derive_behavior_signals(
            EmotionState(joy=60, sadness=10, anger=4, fear=20, disgust=3)
        )

        self.assertEqual(
            signals.to_dict(),
            {
                "warmth": 43,
                "energy": 30,
                "caution": 27,
                "initiative": 26,
                "reflection": 30,
            },
        )

    def test_signals_serialize_as_whole_number_display_values(self):
        signals = derive_behavior_signals(EmotionState(joy=25, sadness=5))

        self.assertEqual(
            set(signals.to_dict()),
            {"warmth", "energy", "caution", "initiative", "reflection"},
        )
        self.assertTrue(all(isinstance(value, int) for value in signals.to_dict().values()))


if __name__ == "__main__":
    unittest.main()
