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
from ikusa_sim.basic_combat import _run_tick, run_basic_combat  # noqa: E402
from ikusa_sim.config_loader import load_config  # noqa: E402
from ikusa_sim.events import event_to_dict  # noqa: E402
from ikusa_sim.models import ConfigBundle, Constants, SkillDef  # noqa: E402
from ikusa_sim.runtime_models import BattleState, UnitState  # noqa: E402


def make_skill(
    skill_id,
    trigger,
    target_rule="current_target",
    cooldown=1.0,
    effect_type="damage",
    effect_value=10,
):
    return SkillDef(
        id=skill_id,
        name=skill_id,
        trigger=trigger,
        target_rule=target_rule,
        cooldown=cooldown,
        effect_type=effect_type,
        effect_value=effect_value,
        tags=[],
    )


def make_config(*skills):
    return ConfigBundle(
        constants=Constants(
            tick_rate=20,
            max_ticks=1200,
            board_rows=3,
            board_cols=4,
            default_seed=1001,
        ),
        units={},
        weapons={},
        skills={skill.id: skill for skill in skills},
        formations={},
        synergies={},
        encounters={},
    )


def make_state(units):
    return BattleState(
        battle_id="test",
        seed=1001,
        tick_rate=20,
        max_ticks=1200,
        current_tick=0,
        units=list(units),
        finished=False,
        result=None,
        _next_event_number=1,
    )


def make_unit(
    instance_id,
    side="ally",
    x=0,
    y=0,
    hp=50,
    atk=12,
    defense=3,
    attack_range=1,
    skill_ids=None,
):
    return UnitState(
        instance_id=instance_id,
        side=side,
        unit_def_id=instance_id,
        x=x,
        y=y,
        role="test",
        name=instance_id,
        tags=[],
        base_hp=hp,
        base_atk=atk,
        base_defense=defense,
        base_range=attack_range,
        base_attack_interval=1.0,
        weapon_slots=[],
        skill_ids=list(skill_ids or []),
        hp=hp,
        alive=True,
        next_action_tick=0,
        action_interval_ticks=20,
    )


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

    def test_lowest_hp_on_attack_skill_does_not_emit_attack_event(self):
        skill = make_skill(
            "focus_fire",
            "on_attack",
            target_rule="lowest_hp_enemy",
            effect_type="focus_fire",
            effect_value=20,
        )
        config = make_config(skill)
        attacker = make_unit("ally_001", x=0, y=0, skill_ids=["focus_fire"])
        selected_by_targeting = make_unit("enemy_same_column", side="enemy", x=0, y=0, hp=100)
        lowest_hp_enemy = make_unit("enemy_low_hp", side="enemy", x=3, y=0, hp=40)
        selected_by_targeting.next_action_tick = 999
        lowest_hp_enemy.next_action_tick = 999
        state = make_state([attacker, selected_by_targeting, lowest_hp_enemy])
        events = []

        _run_tick(state, config, events, tick=0)

        self.assertEqual(["skill_trigger", "damage", "skill_cooldown", "action_scheduled"], [event.type for event in events])
        self.assertEqual(["enemy_low_hp"], events[0].payload["targets"])
        self.assertEqual("enemy_low_hp", events[1].payload["target"])
        self.assertEqual("skill:focus_fire", events[1].payload["reason"])
        self.assertEqual("lowest_hp_enemy", events[0].payload["target_reason"])
        self.assertEqual("focus_fire", events[2].payload["skill"])
        self.assertEqual("ally_001", events[3].payload["unit"])

    def test_current_target_attack_skill_marks_target_reason(self):
        skill = make_skill(
            "katana_slash",
            "on_attack",
            target_rule="current_target",
        )
        config = make_config(skill)
        attacker = make_unit("ally_001", x=0, y=0, hp=90, skill_ids=["katana_slash"])
        target = make_unit("enemy_001", side="enemy", x=0, y=0, hp=40)
        target.next_action_tick = 999
        state = make_state([attacker, target])
        events = []

        _run_tick(state, config, events, tick=0)

        self.assertEqual("skill_trigger", events[0].type)
        self.assertEqual("current_target", events[0].payload["target_reason"])
        self.assertEqual(["enemy_001"], events[0].payload["targets"])
        self.assertIsInstance(events[0].payload.get("target_score"), dict)

    def test_basic_attack_fallback_emits_matching_attack_and_damage_events(self):
        config = make_config()
        attacker = make_unit("ally_001", x=0, y=0)
        target = make_unit("enemy_001", side="enemy", x=0, y=0, hp=40)
        target.next_action_tick = 999
        state = make_state([attacker, target])
        events = []

        _run_tick(state, config, events, tick=0)

        self.assertEqual(["attack", "damage", "action_scheduled"], [event.type for event in events])
        self.assertEqual("basic_attack", events[1].payload["reason"])
        self.assertEqual(events[0].payload["target"], events[1].payload["target"])
        self.assertEqual("frontline_exposed_same_column", events[0].payload["target_reason"])
        self.assertEqual(20, events[2].payload["next_action_tick"])
        self.assertEqual("after_action", events[2].payload["reason"])

    def test_demo_basic_mode_emits_skill_trigger_events(self):
        state, events = self.run_demo()
        event_types = [event.type for event in events]

        self.assertIn("skill_trigger", event_types)
        self.assertIn("status_apply", event_types)
        self.assertIn("skill_cooldown", event_types)
        self.assertIn("action_scheduled", event_types)
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

    def test_skill_combat_emits_stat_modifier_events(self):
        _, events = self.run_demo()
        event_types = {event.type for event in events}

        self.assertIn("stat_modifier", event_types)

    def test_battle_end_payload_keeps_top_level_result_contract(self):
        _, events = self.run_demo()
        battle_end = events[-1]

        self.assertEqual("battle_end", battle_end.type)
        self.assertTrue({"winner", "reason", "end_tick"}.issubset(set(battle_end.payload.keys())))
        self.assertIn("winner_alive", battle_end.payload)
        self.assertIn("loser_alive", battle_end.payload)
        self.assertIn("winner_total_hp", battle_end.payload)
        self.assertIn("loser_total_hp", battle_end.payload)
        self.assertIn("summary", battle_end.payload)


if __name__ == "__main__":
    unittest.main()
