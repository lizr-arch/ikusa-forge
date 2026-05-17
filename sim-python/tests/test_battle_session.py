import json
import sys
import unittest
from collections import Counter
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
from ikusa_sim.battle_session import (  # noqa: E402
    BattleSession,
    build_battle_snapshot,
    create_battle_session,
    get_events_since,
    initialize_battle_session,
    step_battle_session,
    step_until_finished,
)
from ikusa_sim.config_loader import load_config  # noqa: E402
from ikusa_sim.events import event_to_dict  # noqa: E402
from ikusa_sim.report import build_battle_report  # noqa: E402
from ikusa_sim.battle_skeleton import build_replay_document  # noqa: E402


class BattleSessionTests(unittest.TestCase):
    def export_sample_config(self):
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        output_dir = Path(temp_dir.name) / "generated"
        export_tables(REPO_ROOT / "config" / "source", output_dir)
        return output_dir

    def load_sample_bundle(self):
        return load_config(self.export_sample_config())

    def create_session(self):
        return create_battle_session(self.load_sample_bundle(), "demo_001", 1001)

    def test_initialize_battle_session_spawns_units_and_tick_zero_events(self):
        session = self.create_session()

        self.assertIsInstance(session, BattleSession)
        self.assertFalse(session.initialized)
        self.assertFalse(session.finished)
        self.assertEqual(0, len(session.events))

        events = initialize_battle_session(session)
        event_types = [event.type for event in events]

        self.assertTrue(session.initialized)
        self.assertFalse(session.finished)
        self.assertEqual(12, len(session.state.units))
        self.assertEqual(0, session.current_tick)
        self.assertIn("battle_start", event_types)
        self.assertEqual(12, event_types.count("unit_spawn"))
        self.assertIn("stat_modifier", event_types)
        self.assertIn("status_apply", event_types)
        self.assertIn("skill_cooldown", event_types)

    def test_step_battle_session_advances_ticks_and_emits_action_events(self):
        session = self.create_session()
        initialize_battle_session(session)

        first_step_events = step_battle_session(session, ticks=1)
        self.assertEqual(1, session.current_tick)
        self.assertFalse(session.finished)
        self.assertIsInstance(first_step_events, list)

        next_events = step_battle_session(session, ticks=19)
        event_types = [event.type for event in next_events]

        self.assertEqual(20, session.current_tick)
        self.assertFalse(session.finished)
        self.assertTrue(next_events)
        self.assertIn("action_scheduled", event_types)

    def test_repeated_steps_reach_battle_end_once(self):
        session = self.create_session()
        initialize_battle_session(session)

        while not session.finished:
            step_battle_session(session, ticks=5)

        event_types = [event.type for event in session.events]
        self.assertTrue(session.finished)
        self.assertTrue(session.state.finished)
        self.assertEqual("battle_end", session.events[-1].type)
        self.assertEqual(1, event_types.count("battle_end"))
        self.assertEqual("ally", session.state.result.winner)
        self.assertEqual("enemy_eliminated", session.state.result.reason)
        self.assertEqual(240, session.state.result.end_tick)

        after_finished = step_battle_session(session, ticks=10)
        self.assertEqual([], after_finished)

    def test_step_until_finished_matches_run_basic_combat_event_stream(self):
        bundle = self.load_sample_bundle()
        direct_state, direct_events = run_basic_combat(bundle, "demo_001", 1001)

        session = create_battle_session(bundle, "demo_001", 1001)
        initialize_battle_session(session)
        step_until_finished(session)

        self.assertTrue(session.finished)
        self.assertEqual(direct_state.result, session.state.result)
        self.assertEqual(
            [event_to_dict(event) for event in direct_events],
            [event_to_dict(event) for event in session.events],
        )

    def test_step_until_finished_from_uninitialized_session_returns_all_events(self):
        session = self.create_session()

        events = step_until_finished(session)

        self.assertTrue(session.initialized)
        self.assertTrue(session.finished)
        self.assertEqual(len(session.events), len(events))
        self.assertEqual("battle_start", events[0].type)
        self.assertEqual("battle_end", events[-1].type)

    def test_session_report_summary_matches_basic_combat(self):
        bundle = self.load_sample_bundle()
        direct_state, direct_events = run_basic_combat(bundle, "demo_001", 1001)
        direct_timeline = [event_to_dict(event) for event in direct_events]
        direct_report = build_battle_report(build_replay_document(direct_state, direct_events), direct_timeline)

        session = create_battle_session(bundle, "demo_001", 1001)
        step_until_finished(session)
        session_timeline = [event_to_dict(event) for event in session.events]
        session_report = build_battle_report(build_replay_document(session.state, session.events), session_timeline)

        self.assertEqual(direct_report["winner"], session_report["winner"])
        self.assertEqual(direct_report["reason"], session_report["reason"])
        self.assertEqual(direct_report["end_tick"], session_report["end_tick"])
        self.assertEqual(direct_report["summary"], session_report["summary"])
        self.assertEqual(Counter(event["type"] for event in direct_timeline), Counter(event["type"] for event in session_timeline))

    def test_build_battle_snapshot_is_json_safe_and_contains_runtime_state(self):
        session = self.create_session()
        initialize_battle_session(session)
        step_battle_session(session, ticks=20)

        snapshot = build_battle_snapshot(session)
        json.dumps(snapshot)

        self.assertEqual("battle_snapshot.v0.1", snapshot["schema_version"])
        self.assertEqual("demo_001", snapshot["battle_id"])
        self.assertEqual(1001, snapshot["seed"])
        self.assertEqual(20, snapshot["tick"])
        self.assertFalse(snapshot["finished"])
        self.assertIsNone(snapshot["result"])
        self.assertEqual(12, len(snapshot["units"]))
        self.assertEqual(len(session.events), snapshot["event_count"])

        units = snapshot["units"]
        self.assertTrue(any(unit["statuses"] for unit in units))
        self.assertTrue(any(unit["skill_cooldowns"] for unit in units))
        self.assertTrue(any(unit["next_action_tick"] > 0 for unit in units))
        sample_unit = units[0]
        for field in [
            "instance_id",
            "side",
            "unit_def_id",
            "name",
            "x",
            "y",
            "role",
            "hp",
            "base_hp",
            "atk",
            "defense",
            "range",
            "alive",
            "next_action_tick",
            "action_interval_ticks",
            "skill_cooldowns",
            "statuses",
        ]:
            self.assertIn(field, sample_unit)

    def test_get_events_since_uses_integer_event_index_cursor(self):
        session = self.create_session()
        initialize_battle_session(session)

        initial_payload = get_events_since(session, 0)
        self.assertEqual(len(session.events), len(initial_payload["events"]))
        self.assertEqual(len(session.events), initial_payload["next_event_index"])
        self.assertEqual("battle_start", initial_payload["events"][0]["type"])

        old_index = initial_payload["next_event_index"]
        step_battle_session(session, ticks=20)
        delta_payload = get_events_since(session, old_index)

        self.assertGreater(len(delta_payload["events"]), 0)
        self.assertEqual(len(session.events), delta_payload["next_event_index"])
        self.assertIn("action_scheduled", [event["type"] for event in delta_payload["events"]])


if __name__ == "__main__":
    unittest.main()
