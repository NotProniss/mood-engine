import unittest

from mood_engine.response import ResponseGuidance, derive_response_guidance
from mood_engine.state import EmotionState


class ResponseGuidanceTests(unittest.TestCase):
    def test_guidance_contains_focus_intensity_and_string_tone(self):
        guidance = derive_response_guidance(EmotionState())

        self.assertIsInstance(guidance, ResponseGuidance)
        self.assertEqual(
            guidance.to_dict(),
            {"focus": "neutral", "intensity": 0, "tone": "neutral"},
        )
        self.assertIsInstance(guidance.tone, str)
        self.assertEqual(guidance.to_prompt_context(), "focus=neutral; tone=neutral")

    def test_sorrowful_tone_includes_optional_behavior(self):
        guidance = derive_response_guidance(EmotionState(sadness=90))

        self.assertEqual(guidance.tone, "sorrowful")
        self.assertIn("behavior=", guidance.to_prompt_context())
        self.assertIn("Speak gently and reflectively", guidance.to_prompt_context())

    def test_joy_tone_levels(self):
        cases = (
            (1, "content"),
            (24, "content"),
            (25, "happy"),
            (49, "happy"),
            (50, "excited"),
            (64, "excited"),
            (74, "excited"),
            (75, "ecstatic"),
            (100, "ecstatic"),
        )
        for intensity, expected in cases:
            with self.subTest(intensity=intensity):
                guidance = derive_response_guidance(EmotionState(joy=intensity))
                self.assertEqual(guidance.focus, "joy")
                self.assertEqual(guidance.intensity, intensity)
                self.assertEqual(guidance.tone, expected)

    def test_anger_focus_has_its_own_tone(self):
        guidance = derive_response_guidance(EmotionState(anger=80))

        self.assertEqual(guidance.to_dict(), {
            "focus": "anger", "intensity": 80, "tone": "scathing"
        })

    def test_anger_tone_levels(self):
        cases = (
            (1, "annoyed"),
            (24, "annoyed"),
            (25, "irritated"),
            (49, "irritated"),
            (50, "aggressive"),
            (74, "aggressive"),
            (75, "scathing"),
            (100, "scathing"),
        )
        for intensity, expected in cases:
            with self.subTest(intensity=intensity):
                guidance = derive_response_guidance(EmotionState(anger=intensity))
                self.assertEqual(guidance.focus, "anger")
                self.assertEqual(guidance.intensity, intensity)
                self.assertEqual(guidance.tone, expected)

    def test_sadness_tone_levels(self):
        cases = (
            (1, "downcast"),
            (24, "downcast"),
            (25, "sad"),
            (49, "sad"),
            (50, "heavy"),
            (74, "heavy"),
            (75, "sorrowful"),
            (100, "sorrowful"),
        )
        for intensity, expected in cases:
            with self.subTest(intensity=intensity):
                guidance = derive_response_guidance(EmotionState(sadness=intensity))
                self.assertEqual(guidance.focus, "sadness")
                self.assertEqual(guidance.intensity, intensity)
                self.assertEqual(guidance.tone, expected)

    def test_fear_tone_levels(self):
        cases = (
            (1, "uneasy"),
            (24, "uneasy"),
            (25, "wary"),
            (49, "wary"),
            (50, "anxious"),
            (74, "anxious"),
            (75, "horrified"),
            (100, "horrified"),
        )
        for intensity, expected in cases:
            with self.subTest(intensity=intensity):
                guidance = derive_response_guidance(EmotionState(fear=intensity))
                self.assertEqual(guidance.focus, "fear")
                self.assertEqual(guidance.intensity, intensity)
                self.assertEqual(guidance.tone, expected)

    def test_disgust_tone_levels(self):
        cases = (
            (1, "put_off"),
            (24, "put_off"),
            (25, "grossed_out"),
            (49, "grossed_out"),
            (50, "disgusted"),
            (74, "disgusted"),
            (75, "repulsed"),
            (100, "repulsed"),
        )
        for intensity, expected in cases:
            with self.subTest(intensity=intensity):
                guidance = derive_response_guidance(EmotionState(disgust=intensity))
                self.assertEqual(guidance.focus, "disgust")
                self.assertEqual(guidance.intensity, intensity)
                self.assertEqual(guidance.tone, expected)

if __name__ == "__main__":
    unittest.main()
