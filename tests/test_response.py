import unittest

from mood_engine.response import FocusedResponse, derive_focused_response
from mood_engine.state import EmotionState


class FocusedResponseTests(unittest.TestCase):
    def test_all_zero_state_is_neutral(self):
        response = derive_focused_response(EmotionState())
        self.assertIsInstance(response, FocusedResponse)
        self.assertEqual(response.to_dict(), {"focus": "neutral", "intensity": 0, "tone": "neutral", "behavior": None})
        self.assertEqual(response.to_prompt(), "focus=neutral; tone=neutral")

    def test_focus_preserves_raw_intensity(self):
        response = derive_focused_response(EmotionState(joy=23.5, sadness=10))
        self.assertEqual(response.focus, "joy")
        self.assertEqual(response.intensity, 23.5)
        self.assertEqual(response.tone, "content")

    def test_tone_boundaries_are_inclusive(self):
        expected = {1: "content", 24: "content", 25: "happy", 49: "happy", 50: "excited", 74: "excited", 75: "ecstatic", 100: "ecstatic"}
        for intensity, tone in expected.items():
            with self.subTest(intensity=intensity):
                self.assertEqual(derive_focused_response(EmotionState(joy=intensity)).tone, tone)

    def test_highest_raw_value_wins_and_ties_follow_emotion_order(self):
        response = derive_focused_response(EmotionState(joy=50, sadness=75, anger=75))
        self.assertEqual(response.focus, "sadness")
        self.assertEqual(response.intensity, 75)
        self.assertEqual(response.tone, "sorrowful")

    def test_sorrowful_profile_adds_behavior_guidance(self):
        response = derive_focused_response(EmotionState(sadness=75))
        self.assertIn("Speak gently and reflectively", response.to_prompt())


if __name__ == "__main__":
    unittest.main()
