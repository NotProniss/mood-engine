import unittest

from mood_engine.decay import (
    DEFAULT_BASELINES,
    DEFAULT_HALF_LIVES_HOURS,
    decay_state,
)
from mood_engine.state import EmotionState


class DecayTests(unittest.TestCase):
    def test_each_emotion_is_halved_at_its_configured_half_life(self):
        state = EmotionState(joy=80, anger=80, fear=80, disgust=80, sadness=80)

        for emotion, half_life in DEFAULT_HALF_LIVES_HOURS.items():
            decayed = decay_state(state, elapsed_hours=half_life)
            expected = DEFAULT_BASELINES[emotion] + (80 - DEFAULT_BASELINES[emotion]) / 2
            self.assertAlmostEqual(getattr(decayed, emotion), expected)

    def test_decay_moves_values_toward_their_baselines(self):
        state = EmotionState(joy=100, sadness=0)

        decayed = decay_state(state, elapsed_hours=1000)

        self.assertAlmostEqual(decayed.joy, DEFAULT_BASELINES["joy"], places=4)
        self.assertAlmostEqual(decayed.sadness, DEFAULT_BASELINES["sadness"], places=4)

    def test_decay_preserves_fractional_internal_precision_and_floors_display(self):
        state = EmotionState(joy=40)

        decayed = decay_state(state, elapsed_hours=1)

        self.assertGreater(decayed.joy, DEFAULT_BASELINES["joy"])
        self.assertLess(decayed.joy, 40)
        self.assertEqual(decayed.to_display_dict()["joy"], 35)

    def test_zero_elapsed_time_does_not_change_state(self):
        state = EmotionState(joy=42, sadness=17)

        self.assertEqual(decay_state(state, elapsed_hours=0), state)

    def test_decay_rejects_negative_elapsed_time(self):
        with self.assertRaises(ValueError):
            decay_state(EmotionState(joy=10), elapsed_hours=-1)

    def test_decay_stays_within_bounds(self):
        state = EmotionState(joy=100, sadness=100)

        decayed = decay_state(state, elapsed_hours=1000)

        self.assertGreaterEqual(decayed.joy, 0)
        self.assertLessEqual(decayed.joy, 100)
        self.assertGreaterEqual(decayed.sadness, 0)
        self.assertLessEqual(decayed.sadness, 100)


if __name__ == "__main__":
    unittest.main()
