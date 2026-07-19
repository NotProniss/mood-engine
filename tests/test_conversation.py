import unittest

from mood_engine.conversation import ConversationClassification, CONVERSATION_TYPES, classify_round


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
            "pleasant": "pleasant_conversation",
            "funny": "funny_conversation",
            "awkward": "awkward_encounter",
            "unpleasant": "unpleasant_conversation",
            "offensive": "offensive_conversation",
            "hurtful": "hurtful_conversation",
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


if __name__ == "__main__":
    unittest.main()
