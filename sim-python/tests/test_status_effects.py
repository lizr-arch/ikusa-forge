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


class StatusEffectTests(unittest.TestCase):
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

    def test_shield_guard_and_banner_rally_emit_status_apply(self):
        _, events = self.run_demo()
        status_events = [event for event in events if event.type == "status_apply"]

        self.assertTrue(status_events)
        self.assertTrue(
            any(
                event.payload.get("reason") == "skill:shield_guard"
                and event.payload.get("stat") == "guard_value"
                and event.payload.get("target_reason") == "self"
                for event in status_events
            )
        )
        self.assertTrue(
            any(
                event.payload.get("reason") == "skill:banner_rally"
                and event.payload.get("stat") == "atk"
                and event.payload.get("target_reason") == "adjacent_allies"
                for event in status_events
            )
        )

    def test_status_effects_are_stored_on_runtime_units(self):
        state, _ = self.run_demo()
        units_with_status = [unit for unit in state.units if unit.statuses]

        self.assertTrue(units_with_status)
        for unit in units_with_status:
            for status in unit.statuses:
                self.assertEqual(unit.instance_id, status.target)
                self.assertEqual("skill", status.source_type)
                self.assertTrue(status.reason.startswith("skill:"))
                self.assertIsNone(status.expire_tick)

    def test_cooldown_and_action_schedule_payloads_are_explainable(self):
        _, events = self.run_demo()
        cooldown_events = [event for event in events if event.type == "skill_cooldown"]
        schedule_events = [event for event in events if event.type == "action_scheduled"]

        self.assertTrue(cooldown_events)
        self.assertTrue(schedule_events)
        for event in cooldown_events:
            self.assertGreater(event.payload["cooldown_ticks"], 0)
            self.assertEqual(
                event.payload["start_tick"] + event.payload["cooldown_ticks"],
                event.payload["ready_tick"],
            )
        for event in schedule_events:
            self.assertEqual(
                event.payload["current_tick"] + event.payload["action_interval_ticks"],
                event.payload["next_action_tick"],
            )
            self.assertEqual("after_action", event.payload["reason"])

    def test_demo_combat_system_events_are_deterministic(self):
        bundle = self.load_sample_bundle()

        _, first_events = run_basic_combat(bundle, "demo_001", 1001)
        _, second_events = run_basic_combat(bundle, "demo_001", 1001)

        first_combat_system_events = [
            event_to_dict(event)
            for event in first_events
            if event.type in {"status_apply", "skill_cooldown", "action_scheduled", "battle_end"}
        ]
        second_combat_system_events = [
            event_to_dict(event)
            for event in second_events
            if event.type in {"status_apply", "skill_cooldown", "action_scheduled", "battle_end"}
        ]
        self.assertEqual(first_combat_system_events, second_combat_system_events)


if __name__ == "__main__":
    unittest.main()
