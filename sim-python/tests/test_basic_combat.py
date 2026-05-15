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
from ikusa_sim.basic_combat import run_basic_combat  # noqa: E402
from ikusa_sim.battle_skeleton import build_replay_document  # noqa: E402
from ikusa_sim.config_loader import load_config  # noqa: E402
from ikusa_sim.events import event_to_dict  # noqa: E402


class BasicCombatTests(unittest.TestCase):
    def export_sample_config(self):
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        output_dir = Path(temp_dir.name) / "generated"
        export_tables(REPO_ROOT / "config" / "source", output_dir)
        return output_dir

    def load_sample_bundle(self):
        return load_config(self.export_sample_config())

    def run_demo(self):
        return run_basic_combat(self.load_sample_bundle(), "demo_001", 1001)

    def test_demo_basic_combat_emits_combat_events(self):
        state, events = self.run_demo()
        event_types = [event.type for event in events]

        self.assertIn("skill_trigger", event_types)
        self.assertIn("attack", event_types)
        self.assertIn("damage", event_types)
        self.assertIn("death", event_types)
        self.assertEqual("battle_end", events[-1].type)
        self.assertEqual({"winner", "reason", "end_tick"}, set(events[-1].payload.keys()))
        self.assertNotEqual("timeout_no_combat", events[-1].payload["reason"])
        self.assertTrue(state.finished)

    def test_same_config_battle_and_seed_emit_identical_basic_events(self):
        bundle = self.load_sample_bundle()

        _, first_events = run_basic_combat(bundle, "demo_001", 1001)
        _, second_events = run_basic_combat(bundle, "demo_001", 1001)

        self.assertEqual(
            [event_to_dict(event) for event in first_events],
            [event_to_dict(event) for event in second_events],
        )

    def test_basic_event_ids_are_stable_and_sequential(self):
        _, events = self.run_demo()

        self.assertEqual(
            ["evt_{:06d}".format(index) for index in range(1, len(events) + 1)],
            [event.event_id for event in events],
        )

    def test_basic_combat_does_not_emit_future_out_of_scope_events(self):
        _, events = self.run_demo()
        event_types = {event.type for event in events}

        self.assertNotIn("synergy", event_types)
        self.assertNotIn("formation_bonus", event_types)

    def test_basic_combat_damage_events_include_reason(self):
        _, events = self.run_demo()
        damage_events = [event for event in events if event.type == "damage"]

        self.assertTrue(damage_events)
        self.assertTrue(all("reason" in event.payload for event in damage_events))
        self.assertTrue(
            any(event.payload["reason"].startswith("skill:") for event in damage_events)
        )

    def test_basic_replay_metadata_keeps_result_object(self):
        state, events = self.run_demo()
        metadata_result = build_replay_document(state, events)["metadata"]["result"]

        self.assertIn("winner", metadata_result)
        self.assertIn("reason", metadata_result)
        self.assertIn("end_tick", metadata_result)


if __name__ == "__main__":
    unittest.main()
