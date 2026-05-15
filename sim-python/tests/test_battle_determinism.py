import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
TOOLS_DIR = REPO_ROOT / "tools"
for path in (SIM_DIR, TOOLS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from export_xlsx_to_json import export_tables  # noqa: E402
from ikusa_sim.battle_skeleton import build_replay_document, run_battle_skeleton  # noqa: E402
from ikusa_sim.config_loader import load_config  # noqa: E402
from ikusa_sim.events import event_to_dict  # noqa: E402


class BattleDeterminismTests(unittest.TestCase):
    def export_sample_config(self):
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        output_dir = Path(temp_dir.name) / "generated"
        export_tables(REPO_ROOT / "config" / "source", output_dir)
        return output_dir

    def load_sample_bundle(self):
        return load_config(self.export_sample_config())

    def test_same_config_battle_and_seed_emit_identical_events(self):
        bundle = self.load_sample_bundle()

        _, first_events = run_battle_skeleton(bundle, "demo_001", 1001)
        _, second_events = run_battle_skeleton(bundle, "demo_001", 1001)

        self.assertEqual(
            [event_to_dict(event) for event in first_events],
            [event_to_dict(event) for event in second_events],
        )

    def test_replay_metadata_records_requested_seed(self):
        bundle = self.load_sample_bundle()

        first_state, first_events = run_battle_skeleton(bundle, "demo_001", 1001)
        second_state, second_events = run_battle_skeleton(bundle, "demo_001", 2002)

        self.assertEqual(1001, build_replay_document(first_state, first_events)["metadata"]["seed"])
        self.assertEqual(2002, build_replay_document(second_state, second_events)["metadata"]["seed"])

    def test_skeleton_replay_metadata_keeps_result_object(self):
        state, events = run_battle_skeleton(self.load_sample_bundle(), "demo_001", 1001)
        metadata_result = build_replay_document(state, events)["metadata"]["result"]

        self.assertEqual("draw", metadata_result["winner"])
        self.assertEqual("timeout_no_combat", metadata_result["reason"])
        self.assertEqual(state.max_ticks, metadata_result["end_tick"])


if __name__ == "__main__":
    unittest.main()
