import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from mood_engine.events import EventRules
from mood_engine.runtime import AffectRuntime
from mood_engine.state import EmotionState


RULES_PATH = Path(__file__).parents[1] / "config" / "emotion_rules.json"
UTC = timezone.utc


class PersistentAffectRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rules = EventRules.from_json_file(RULES_PATH)

    def test_save_and_reload_preserves_runtime_state(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            timestamp = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
            runtime = AffectRuntime(
                state=EmotionState(joy=42.5, sadness=8.0),
                event_rules=self.rules,
            )

            runtime.save_state(path, updated_at=timestamp)
            restored = AffectRuntime.from_state_file(
                path,
                now=timestamp,
                event_rules=self.rules,
            )

            self.assertEqual(restored.state, runtime.state)
            self.assertEqual(restored.updated_at, timestamp)

    def test_reload_applies_decay_before_future_event_processing(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            saved_at = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
            now = saved_at + timedelta(hours=6)
            runtime = AffectRuntime(
                state=EmotionState(joy=80),
                event_rules=self.rules,
            )
            runtime.save_state(path, updated_at=saved_at)

            restored = AffectRuntime.from_state_file(
                path,
                now=now,
                event_rules=self.rules,
            )
            snapshot = restored.process_event("funny_conversation")

            self.assertAlmostEqual(snapshot.state.joy, 42.0)
            self.assertEqual(restored.updated_at, now)

    def test_reload_uses_the_runtime_baseline_configuration(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            saved_at = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
            now = saved_at + timedelta(hours=6)
            runtime = AffectRuntime(
                state=EmotionState(joy=80),
                event_rules=self.rules,
            )
            runtime.save_state(path, updated_at=saved_at)

            restored = AffectRuntime.from_state_file(
                path,
                now=now,
                event_rules=self.rules,
                baselines={
                    "joy": 10,
                    "sadness": 5,
                    "anger": 2,
                    "fear": 3,
                    "disgust": 1,
                },
            )

            self.assertAlmostEqual(restored.state.joy, 45.0)

    def test_save_after_processing_writes_updated_state(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            timestamp = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
            runtime = AffectRuntime(event_rules=self.rules)
            runtime.process_event("funny_conversation")

            runtime.save_state(path, updated_at=timestamp)
            restored = AffectRuntime.from_state_file(
                path,
                now=timestamp,
                event_rules=self.rules,
            )

            self.assertEqual(restored.state.joy, 2)
            self.assertEqual(restored.state.sadness, 0)


if __name__ == "__main__":
    unittest.main()
