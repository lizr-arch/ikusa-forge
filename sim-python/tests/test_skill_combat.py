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
from ikusa_sim.config_loader import load_config  # noqa: E402
from ikusa_sim.events import event_to_dict  # noqa: E402


class SkillCombatTests(unittest.TestCase):
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

    def test_demo_basic_mode_emits_skill_trigger_events(self):
        state, events = self.run_demo()
        event_types = [event.type for event in events]

        self.assertIn("skill_trigger", event_types)
        self.assertEqual("battle_end", events[-1].type)
        self.assertTrue(state.finished)

    def test_demo_damage_events_include_skill_reason(self):
        _, events = self.run_demo()
        damage_reasons = [
            event.payload["reason"]
            for event in events
            if event.type == "damage"
        ]

        self.assertTrue(any(reason.startswith("skill:") for reason in damage_reasons))
        self.assertTrue(all(reason for reason in damage_reasons))

    def test_same_config_battle_and_seed_emit_identical_skill_events(self):
        bundle = self.load_sample_bundle()

        _, first_events = run_basic_combat(bundle, "demo_001", 1001)
        _, second_events = run_basic_combat(bundle, "demo_001", 1001)

        self.assertEqual(
            [event_to_dict(event) for event in first_events],
            [event_to_dict(event) for event in second_events],
        )

    def test_skill_event_ids_are_stable_and_sequential(self):
        _, events = self.run_demo()

        self.assertEqual(
            ["evt_{:06d}".format(index) for index in range(1, len(events) + 1)],
            [event.event_id for event in events],
        )

    def test_skill_combat_does_not_emit_out_of_scope_rule_events(self):
        _, events = self.run_demo()
        event_types = {event.type for event in events}

        self.assertNotIn("synergy", event_types)
        self.assertNotIn("formation_bonus", event_types)

    def test_battle_end_payload_keeps_top_level_result_contract(self):
        _, events = self.run_demo()
        battle_end = events[-1]

        self.assertEqual("battle_end", battle_end.type)
        self.assertEqual({"winner", "reason", "end_tick"}, set(battle_end.payload.keys()))


if __name__ == "__main__":
    unittest.main()
