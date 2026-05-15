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
from ikusa_sim.battle import events_to_tick_groups, run_battle_skeleton  # noqa: E402
from ikusa_sim.config_loader import load_config  # noqa: E402


class BattleSkeletonTests(unittest.TestCase):
    def export_sample_config(self):
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        output_dir = Path(temp_dir.name) / "generated"
        export_tables(REPO_ROOT / "config" / "source", output_dir)
        return output_dir

    def load_sample_bundle(self):
        return load_config(self.export_sample_config())

    def run_demo(self):
        return run_battle_skeleton(self.load_sample_bundle(), "demo_001", 1001)

    def test_demo_creates_twelve_runtime_units(self):
        state, events = self.run_demo()
        instance_ids = {unit.instance_id for unit in state.units}

        self.assertEqual(12, len(state.units))
        self.assertIn("ally_001", instance_ids)
        self.assertIn("enemy_001", instance_ids)
        self.assertTrue(all(unit.role for unit in state.units))
        self.assertEqual(0, events[0].tick)
        self.assertEqual(state.max_ticks, state.current_tick)

    def test_demo_emits_minimal_event_stream(self):
        state, events = self.run_demo()
        event_types = [event.type for event in events]

        self.assertEqual(1, event_types.count("battle_start"))
        self.assertEqual(12, event_types.count("unit_spawn"))
        self.assertEqual(1, event_types.count("battle_end"))
        self.assertEqual(
            ["evt_{:06d}".format(index) for index in range(1, 15)],
            [event.event_id for event in events],
        )

        battle_end = events[-1]
        self.assertEqual("battle_end", battle_end.type)
        self.assertEqual(state.max_ticks, battle_end.tick)
        self.assertEqual("draw", battle_end.payload["result"]["winner"])
        self.assertEqual("timeout_no_combat", battle_end.payload["result"]["reason"])

    def test_events_group_by_tick_without_reordering(self):
        state, events = self.run_demo()
        groups = events_to_tick_groups(events)

        self.assertEqual([0, state.max_ticks], [group["tick"] for group in groups])
        self.assertEqual("battle_start", groups[0]["events"][0]["type"])
        self.assertEqual("unit_spawn", groups[0]["events"][1]["type"])
        self.assertEqual("battle_end", groups[1]["events"][0]["type"])


if __name__ == "__main__":
    unittest.main()
