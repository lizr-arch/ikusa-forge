import json
import sys
import unittest
from collections import Counter
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
TOOLS_DIR = REPO_ROOT / "tools"
for path in (SIM_DIR, TOOLS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from export_xlsx_to_json import export_tables  # noqa: E402
from ikusa_sim.report import build_battle_report  # noqa: E402
from run_demo_battle import main as run_demo_main  # noqa: E402


def make_replay_doc():
    return {
        "schema_version": "battle_replay.v0.1",
        "metadata": {
            "battle_id": "test_battle",
            "seed": 1001,
            "result": {
                "winner": "ally",
                "reason": "enemy_eliminated",
                "end_tick": 42,
            },
        },
        "ticks": [],
    }


def make_events():
    return [
        {
            "tick": 0,
            "event_id": "evt_000001",
            "type": "unit_spawn",
            "payload": {"unit": {"instance_id": "ally_001"}},
        },
        {
            "tick": 0,
            "event_id": "evt_000002",
            "type": "unit_spawn",
            "payload": {"unit": {"instance_id": "enemy_001"}},
        },
        {
            "tick": 10,
            "event_id": "evt_000003",
            "type": "skill_trigger",
            "payload": {
                "source": "ally_001",
                "skill": "katana_slash",
                "trigger": "on_attack",
                "targets": ["enemy_001"],
                "target_reason": "current_target",
            },
        },
        {
            "tick": 10,
            "event_id": "evt_000003_status",
            "type": "status_apply",
            "payload": {
                "id": "status_ally_001_katana_slash_001",
                "source": "ally_001",
                "source_type": "skill",
                "target": "ally_001",
                "stat": "atk",
                "amount": 3,
                "start_tick": 10,
                "expire_tick": None,
                "reason": "skill:katana_slash",
                "target_reason": "self",
            },
        },
        {
            "tick": 10,
            "event_id": "evt_000003_1",
            "type": "attack",
            "payload": {
                "attacker": "ally_001",
                "target": "enemy_001",
                "target_reason": "frontline_exposed_same_column",
            },
        },
        {
            "tick": 10,
            "event_id": "evt_000004",
            "type": "damage",
            "payload": {
                "source": "ally_001",
                "target": "enemy_001",
                "amount": 30,
                "target_hp_after": 20,
                "reason": "skill:katana_slash",
            },
        },
        {
            "tick": 10,
            "event_id": "evt_000004_cooldown",
            "type": "skill_cooldown",
            "payload": {
                "source": "ally_001",
                "skill": "katana_slash",
                "start_tick": 10,
                "ready_tick": 30,
                "cooldown_ticks": 20,
            },
        },
        {
            "tick": 10,
            "event_id": "evt_000004_action",
            "type": "action_scheduled",
            "payload": {
                "unit": "ally_001",
                "current_tick": 10,
                "next_action_tick": 30,
                "action_interval_ticks": 20,
                "reason": "after_action",
            },
        },
        {
            "tick": 12,
            "event_id": "evt_000005",
            "type": "damage",
            "payload": {
                "source": "enemy_001",
                "target": "ally_001",
                "amount": 5,
                "target_hp_after": 95,
                "reason": "basic_attack",
            },
        },
        {
            "tick": 20,
            "event_id": "evt_000006",
            "type": "damage",
            "payload": {
                "source": "ally_001",
                "target": "enemy_001",
                "amount": 25,
                "target_hp_after": 0,
                "reason": "basic_attack",
            },
        },
        {
            "tick": 20,
            "event_id": "evt_000007",
            "type": "death",
            "payload": {"unit": "enemy_001"},
        },
        {
            "tick": 42,
            "event_id": "evt_000008",
            "type": "battle_end",
            "payload": {
                "winner": "ally",
                "reason": "enemy_eliminated",
                "end_tick": 42,
                "winner_alive": 1,
                "loser_alive": 0,
                "winner_total_hp": 95,
                "loser_total_hp": 0,
                "summary": "ally won by enemy_eliminated at tick 42",
            },
        },
    ]


class BattleReportTests(unittest.TestCase):
    def build_report(self):
        return build_battle_report(make_replay_doc(), make_events())

    def test_damage_done_aggregates_by_source(self):
        report = self.build_report()

        self.assertEqual(55, report["units"]["ally_001"]["damage_done"])
        self.assertEqual(5, report["units"]["enemy_001"]["damage_done"])
        self.assertEqual(60, report["summary"]["total_damage"])

    def test_damage_taken_aggregates_by_target(self):
        report = self.build_report()

        self.assertEqual(55, report["units"]["enemy_001"]["damage_taken"])
        self.assertEqual(5, report["units"]["ally_001"]["damage_taken"])

    def test_kills_use_last_damage_source_before_death(self):
        report = self.build_report()
        death_moment = [
            moment for moment in report["key_moments"] if moment["type"] == "death"
        ][0]

        self.assertEqual(1, report["units"]["ally_001"]["kills"])
        self.assertEqual(1, report["summary"]["total_kills"])
        self.assertEqual("ally_001", death_moment["killer"])
        self.assertIn("enemy_001 was killed by ally_001", death_moment["summary"])

    def test_skill_triggers_aggregate_by_source_and_skill(self):
        report = self.build_report()

        self.assertEqual(
            {"katana_slash": 1},
            report["units"]["ally_001"]["skill_triggers"],
        )
        self.assertEqual(1, report["summary"]["total_skill_triggers"])
        self.assertEqual(1, report["summary"]["total_skill_cooldowns"])
        self.assertEqual(1, report["units"]["ally_001"]["cooldowns_started"])

    def test_target_reason_counts_are_aggregated(self):
        report = self.build_report()

        self.assertIn("target_reason_counts", report["summary"])
        self.assertEqual({"frontline_exposed_same_column": 1}, report["summary"]["target_reason_counts"])

    def test_skill_target_reason_counts_are_aggregated(self):
        report = self.build_report()

        self.assertIn("skill_target_reason_counts", report["summary"])
        self.assertEqual({"current_target": 1}, report["summary"]["skill_target_reason_counts"])

    def test_battle_end_result_goes_to_top_level_report(self):
        report = self.build_report()
        battle_end_moment = [
            moment for moment in report["key_moments"] if moment["type"] == "battle_end"
        ][0]

        self.assertEqual("ally", report["winner"])
        self.assertEqual("enemy_eliminated", report["reason"])
        self.assertEqual(42, report["end_tick"])
        self.assertEqual("ally", battle_end_moment["winner"])
        self.assertEqual("ally", report["victory_explanation"]["winner"])
        self.assertEqual(1, report["victory_explanation"]["winner_alive"])
        self.assertIn("ally won", report["victory_explanation"]["summary"])

    def test_status_and_action_counts_are_aggregated(self):
        report = self.build_report()

        self.assertEqual(1, report["summary"]["total_status_applied"])
        self.assertEqual(0, report["summary"]["total_status_expired"])
        self.assertEqual(1, report["summary"]["total_actions_scheduled"])
        self.assertEqual(1, report["units"]["ally_001"]["statuses_applied"])
        self.assertEqual(1, report["units"]["ally_001"]["actions_taken"])
        self.assertEqual(30, report["units"]["ally_001"]["last_next_action_tick"])

    def test_demo_run_writes_basic_and_skeleton_reports(self):
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_dir = temp_path / "generated"
            basic_out = temp_path / "basic_run"
            skeleton_out = temp_path / "skeleton_run"
            export_tables(REPO_ROOT / "config" / "source", config_dir)

            with redirect_stdout(StringIO()):
                basic_result = run_demo_main(
                    [
                        "--battle",
                        "demo_001",
                        "--seed",
                        "1001",
                        "--config",
                        str(config_dir),
                        "--out",
                        str(basic_out),
                        "--mode",
                        "basic",
                    ]
                )
                skeleton_result = run_demo_main(
                    [
                        "--battle",
                        "demo_001",
                        "--seed",
                        "1001",
                        "--config",
                        str(config_dir),
                        "--out",
                        str(skeleton_out),
                        "--mode",
                        "skeleton",
                    ]
                )

            basic_report = json.loads(
                (basic_out / "battle_report.json").read_text(encoding="utf-8")
            )
            skeleton_report = json.loads(
                (skeleton_out / "battle_report.json").read_text(encoding="utf-8")
            )

        self.assertEqual(0, basic_result)
        self.assertEqual(0, skeleton_result)
        self.assertEqual("ally", basic_report["winner"])
        self.assertGreater(basic_report["summary"]["total_damage"], 0)
        self.assertGreater(basic_report["summary"]["total_skill_triggers"], 0)
        self.assertGreater(basic_report["summary"]["total_status_applied"], 0)
        self.assertGreater(basic_report["summary"]["total_skill_cooldowns"], 0)
        self.assertGreater(basic_report["summary"]["total_actions_scheduled"], 0)
        self.assertGreater(basic_report["summary"]["total_modifiers"], 0)
        self.assertGreater(basic_report["summary"]["formation_modifiers"], 0)
        self.assertGreater(basic_report["summary"]["synergy_modifiers"], 0)
        self.assertIn("victory_explanation", basic_report)
        self.assertTrue(basic_report["key_moments"])
        self.assertEqual(0, skeleton_report["summary"]["total_damage"])
        self.assertEqual(0, skeleton_report["summary"]["total_kills"])
        self.assertEqual(0, skeleton_report["summary"]["total_skill_triggers"])
        self.assertEqual(0, skeleton_report["summary"].get("total_status_applied", 0))
        self.assertEqual(0, skeleton_report["summary"].get("total_skill_cooldowns", 0))
        self.assertEqual(0, skeleton_report["summary"].get("total_actions_scheduled", 0))
        self.assertEqual(0, skeleton_report["summary"].get("total_modifiers", 0))
        self.assertEqual(0, skeleton_report["summary"].get("formation_modifiers", 0))
        self.assertEqual(0, skeleton_report["summary"].get("synergy_modifiers", 0))

    def test_demo_integration_has_form_and_syn_source_modifiers(self) -> None:
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_dir = temp_path / "generated"
            basic_out = temp_path / "demo_run"
            export_tables(REPO_ROOT / "config" / "source", config_dir)

            with redirect_stdout(StringIO()):
                run_demo_main(
                    [
                        "--battle",
                        "demo_001",
                        "--seed",
                        "1001",
                        "--config",
                        str(config_dir),
                        "--out",
                        str(basic_out),
                        "--mode",
                        "basic",
                    ]
                )

            debug_timeline = json.loads(
                (basic_out / "debug_timeline.json").read_text(encoding="utf-8")
            )
            modifier_sources = Counter(
                event["payload"].get("source_type")
                for event in debug_timeline
                if event.get("type") == "stat_modifier"
            )

            self.assertGreater(len([event for event in debug_timeline if event.get("type") == "stat_modifier"]), 0)
            self.assertGreater(modifier_sources.get("formation", 0), 0)
            self.assertGreater(modifier_sources.get("synergy", 0), 0)
            self.assertTrue(
                any(
                    event["payload"].get("stat") == "hp"
                    for event in debug_timeline
                    if event.get("type") == "stat_modifier"
                )
            )


if __name__ == "__main__":
    unittest.main()
