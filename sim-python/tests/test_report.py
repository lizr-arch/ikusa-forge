import json
import sys
import unittest
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

    def test_battle_end_result_goes_to_top_level_report(self):
        report = self.build_report()
        battle_end_moment = [
            moment for moment in report["key_moments"] if moment["type"] == "battle_end"
        ][0]

        self.assertEqual("ally", report["winner"])
        self.assertEqual("enemy_eliminated", report["reason"])
        self.assertEqual(42, report["end_tick"])
        self.assertEqual("ally", battle_end_moment["winner"])

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
        self.assertTrue(basic_report["key_moments"])
        self.assertEqual(0, skeleton_report["summary"]["total_damage"])
        self.assertEqual(0, skeleton_report["summary"]["total_kills"])
        self.assertEqual(0, skeleton_report["summary"]["total_skill_triggers"])


if __name__ == "__main__":
    unittest.main()
