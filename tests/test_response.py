import unittest

from mood_engine.behavior import BehaviorSignals
from mood_engine.response import ResponseGuidance, derive_response_guidance


class ResponseGuidanceTests(unittest.TestCase):
    def test_positive_expression_produces_warm_lively_guidance(self):
        guidance = derive_response_guidance(
            BehaviorSignals(
                warmth=40,
                energy=30,
                caution=5,
                initiative=35,
                reflection=5,
            )
        )

        self.assertIsInstance(guidance, ResponseGuidance)
        self.assertEqual(guidance.tone, "warm")
        self.assertEqual(guidance.energy, "lively")
        self.assertEqual(guidance.stance, "open")
        self.assertEqual(guidance.initiative, "proactive")
        self.assertEqual(guidance.reflection, "low")

    def test_distressed_expression_produces_careful_reflective_guidance(self):
        guidance = derive_response_guidance(
            BehaviorSignals(
                warmth=-20,
                energy=-35,
                caution=50,
                initiative=-30,
                reflection=45,
            )
        )

        self.assertEqual(guidance.tone, "reserved")
        self.assertEqual(guidance.energy, "quiet")
        self.assertEqual(guidance.stance, "careful")
        self.assertEqual(guidance.initiative, "responsive")
        self.assertEqual(guidance.reflection, "reflective")

    def test_guidance_serializes_to_inspectable_dict(self):
        guidance = derive_response_guidance(BehaviorSignals(0, 0, 0, 0, 0))

        self.assertEqual(
            set(guidance.to_dict()),
            {"tone", "energy", "stance", "initiative", "reflection"},
        )


if __name__ == "__main__":
    unittest.main()
