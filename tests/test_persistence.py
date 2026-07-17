import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from mood_engine.persistence import StateFileError, load_state, save_state
from mood_engine.state import EmotionState


UTC = timezone.utc


class PersistenceTests(unittest.TestCase):
    def test_save_and_load_preserves_state_and_timestamp(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            updated_at = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
            original = EmotionState(joy=42.75, sadness=8.25)

            save_state(path, original, updated_at)
            restored, restored_at = load_state(path, now=updated_at)

            self.assertEqual(restored, original)
            self.assertEqual(restored_at, updated_at)

    def test_load_applies_decay_since_last_update(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            updated_at = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)
            now = updated_at + timedelta(hours=6)

            save_state(path, EmotionState(joy=80), updated_at)
            restored, restored_at = load_state(path, now=now)

            self.assertAlmostEqual(restored.joy, 52.5)
            self.assertEqual(restored_at, now)

    def test_malformed_state_raises_clear_error(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text("not valid json", encoding="utf-8")

            with self.assertRaises(StateFileError):
                load_state(path, now=datetime.now(UTC))

    def test_saved_file_is_inspectable_json(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            save_state(
                path,
                EmotionState(fear=12.5),
                datetime(2026, 7, 16, 12, 0, tzinfo=UTC),
            )

            payload = json.loads(path.read_text(encoding="utf-8"))

            self.assertEqual(payload["version"], 1)
            self.assertEqual(payload["emotions"]["fear"], 12.5)
            self.assertIn("updated_at", payload)


if __name__ == "__main__":
    unittest.main()
