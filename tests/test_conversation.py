import unittest
from types import SimpleNamespace

from mood_engine.conversation import (
    CONVERSATION_TYPES,
    ConversationClassification,
    classify_round,
    classify_round_with_semantics,
)


class ConversationClassificationTests(unittest.TestCase):
    def test_ordinary_round_is_casual_and_has_no_event(self):
        result = classify_round("Hey, how are you?", "I'm doing well.")
        self.assertEqual(result, ConversationClassification("casual", 0.9))
        self.assertTrue(result.is_casual)
        self.assertIsNone(result.event_name)

    def test_all_supported_types_are_known(self):
        self.assertEqual(
            CONVERSATION_TYPES,
            ("casual", "pleasant", "funny", "awkward", "unpleasant", "offensive", "hurtful"),
        )

    def test_each_non_casual_type_maps_to_one_event(self):
        examples = {
            "pleasant": "Thanks, that helps a lot.",
            "funny": "That was hilarious, haha.",
            "awkward": "That was really awkward.",
            "unpleasant": "This is disgusting.",
            "offensive": "That was rude and insulting.",
            "hurtful": "That hurt and made me sad.",
        }
        expected_events = {
            "pleasant": "pleasant",
            "funny": "funny",
            "awkward": "awkward",
            "unpleasant": "unpleasant",
            "offensive": "offensive",
            "hurtful": "hurtful",
        }
        for kind, message in examples.items():
            with self.subTest(kind=kind):
                result = classify_round(message)
                self.assertEqual(result.conversation_type, kind)
                self.assertEqual(result.event_name, expected_events[kind])
                self.assertGreaterEqual(result.confidence, 0.8)

    def test_priority_prefers_hurtful_over_positive_language(self):
        result = classify_round("Thanks, but that hurt me.")
        self.assertEqual(result.conversation_type, "hurtful")

    def test_assistant_response_does_not_create_events_by_itself(self):
        result = classify_round("Okay.", "That was hilarious, haha!")
        self.assertTrue(result.is_casual)

    def test_expanded_word_banks_cover_natural_phrases(self):
        examples = {
            "pleasant": "I really enjoyed talking with you.",
            "funny": "That cracked me up.",
            "awkward": "I don't know what to say.",
            "unpleasant": "That was really irritating.",
            "offensive": "You were being condescending.",
            "hurtful": "You hurt my feelings.",
        }
        for kind, message in examples.items():
            with self.subTest(kind=kind):
                self.assertEqual(classify_round(message).conversation_type, kind)

    def test_semantic_classifier_uses_emotion_rules_labels(self):
        class FakeLLM:
            def complete_structured(self, **kwargs):
                self.schema = kwargs["json_schema"]
                return SimpleNamespace(
                    parsed={
                        "conversation_type": "pleasant",
                        "confidence": 0.91,
                        "intensity": 0.4,
                    }
                )

        context = SimpleNamespace(llm=FakeLLM())
        result = classify_round_with_semantics(context, "That was nice.")

        self.assertEqual(result, ConversationClassification("pleasant", 0.91, 0.4, "pleasant"))
        self.assertEqual(context.llm.schema["properties"]["conversation_type"]["enum"], list(CONVERSATION_TYPES))

    def test_low_confidence_semantic_result_falls_back_to_rules(self):
        class FakeLLM:
            def complete_structured(self, **_kwargs):
                return SimpleNamespace(
                    parsed={
                        "conversation_type": "pleasant",
                        "confidence": 0.2,
                        "intensity": 0.4,
                    }
                )

        result = classify_round_with_semantics(SimpleNamespace(llm=FakeLLM()), "Thanks, that helps.")
        self.assertEqual(result.conversation_type, "pleasant")
        self.assertEqual(result.event_name, "pleasant")

    def test_ambiguous_short_replies_remain_casual(self):
        for message in ("fine", "okay", "sure", "yep", "I see"):
            with self.subTest(message=message):
                self.assertTrue(classify_round(message).is_casual)


if __name__ == "__main__":
    unittest.main()
