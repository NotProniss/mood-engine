import unittest
from pathlib import Path

from mood_engine.decay import load_half_lives


CONFIG_PATH = Path(__file__).parents[1] / "config" / "decay_rules.json"


class DecayConfigTests(unittest.TestCase):
    def test_default_config_contains_all_emotions(self):
        half_lives = load_half_lives(CONFIG_PATH)

        self.assertEqual(
            set(half_lives),
            {"joy", "sadness", "anger", "fear", "disgust"},
        )

    def test_config_values_are_positive_numbers(self):
        half_lives = load_half_lives(CONFIG_PATH)

        self.assertTrue(all(value > 0 for value in half_lives.values()))


if __name__ == "__main__":
    unittest.main()
