import json
import sys
import unittest
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
TOOLS_DIR = REPO_ROOT / "tools"
for path in (SIM_DIR, TOOLS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from export_xlsx_to_json import export_tables  # noqa: E402
from ikusa_sim.action_pipeline import (  # noqa: E402
    build_basic_attack_action as pipeline_build_basic_attack,
    build_skill_action as pipeline_build_skill,
    emit_events_from_effects,
    run_combat_action,
    validate_combat_action,
)
from ikusa_sim.actions import (  # noqa: E402
    ActionResult,
    CombatAction,
    build_basic_attack_action,
)
from ikusa_sim.basic_combat import run_basic_combat  # noqa: E402
from ikusa_sim.config_loader import load_config  # noqa: E402
from ikusa_sim.effect_models import (  # noqa: E402
    ActionScheduleEffect,
    CooldownEffect,
    DamageEffect,
    DeathEffect,
    StatusApplyEffect,
)
from ikusa_sim.events import BattleEvent  # noqa: E402
from ikusa_sim.models import ConfigBundle, Constants, SkillDef  # noqa: E402
from ikusa_sim.runtime_models import BattleState, UnitState  # noqa: E402


def make_skill(skill_id, trigger="on_attack", target_rule="current_target", cooldown=1.0, effect_type="damage", effect_value=10):
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
    attack_range=18.0,
    skill_ids=None,
    position_x=None,
    position_y=None,
    next_action_tick=0,
    action_interval_ticks=20,
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
        base_range=1,
        base_attack_interval=1.0,
        weapon_slots=[],
        skill_ids=list(skill_ids or []),
        hp=hp,
        alive=True,
        next_action_tick=next_action_tick,
        action_interval_ticks=action_interval_ticks,
        position_x=position_x if position_x is not None else float(x),
        position_y=position_y if position_y is not None else float(y),
        attack_range=attack_range,
    )


class ActionPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._temp_dir = TemporaryDirectory()
        cls.generated_dir = Path(cls._temp_dir.name) / "generated"
        export_tables(REPO_ROOT / "config" / "source", cls.generated_dir)
        cls.bundle = load_config(cls.generated_dir)

    @classmethod
    def tearDownClass(cls):
        cls._temp_dir.cleanup()

    def test_basic_attack_through_pipeline(self):
        attacker = make_unit("ally_001", x=0, y=0, position_x=0.0, position_y=0.0, attack_range=18.0)
        target = make_unit("enemy_001", side="enemy", x=0, y=0, position_x=10.0, position_y=0.0, hp=100, attack_range=18.0)
        target.next_action_tick = 999
        state = make_state([attacker, target])
        events: List[BattleEvent] = []

        action = pipeline_build_basic_attack(state, attacker, target, tick=1)
        validate_result = validate_combat_action(state, action)
        self.assertTrue(validate_result.ok)

        result = run_combat_action(state, action, 1, events)
        self.assertTrue(result.ok)
        event_types = [e.type for e in events]
        self.assertIn("attack", event_types)
        self.assertIn("damage", event_types)
        self.assertLess(target.hp, 100)

    def test_out_of_range_validation(self):
        attacker = make_unit("ally_001", x=0, y=0, position_x=0.0, position_y=0.0, attack_range=18.0)
        target = make_unit("enemy_001", side="enemy", x=0, y=0, position_x=100.0, position_y=0.0, attack_range=18.0)
        state = make_state([attacker, target])
        events: List[BattleEvent] = []

        action = pipeline_build_basic_attack(state, attacker, target, tick=1)
        validate_result = validate_combat_action(state, action)
        self.assertFalse(validate_result.ok)

        result = run_combat_action(state, action, 1, events)
        self.assertFalse(result.ok)
        self.assertEqual(0, len([e for e in events if e.type == "damage"]))

    def test_skill_action_through_pipeline(self):
        skill = make_skill("fire_bolt", effect_type="damage", effect_value=20, cooldown=1.0)
        attacker = make_unit("ally_001", x=0, y=0, position_x=0.0, position_y=0.0, attack_range=18.0, skill_ids=["fire_bolt"])
        target = make_unit("enemy_001", side="enemy", x=0, y=0, position_x=10.0, position_y=0.0, hp=100, attack_range=18.0)
        state = make_state([attacker, target])
        events: List[BattleEvent] = []

        action = pipeline_build_skill(state, attacker, skill, [target], tick=1)
        result = run_combat_action(state, action, 1, events)

        self.assertTrue(result.ok)
        event_types = [e.type for e in events]
        self.assertIn("skill_trigger", event_types)
        self.assertIn("damage", event_types)
        self.assertIn("skill_cooldown", event_types)

    def test_death_effect_through_pipeline(self):
        attacker = make_unit("ally_001", x=0, y=0, position_x=0.0, position_y=0.0, attack_range=18.0, atk=100)
        target = make_unit("enemy_001", side="enemy", x=0, y=0, position_x=10.0, position_y=0.0, hp=5, defense=0, attack_range=18.0)
        target.next_action_tick = 999
        state = make_state([attacker, target])
        events: List[BattleEvent] = []

        action = pipeline_build_basic_attack(state, attacker, target, tick=1)
        result = run_combat_action(state, action, 1, events)

        self.assertTrue(result.ok)
        event_types = [e.type for e in events]
        self.assertIn("death", event_types)
        self.assertFalse(target.alive)

    def test_action_scheduled_event_fields(self):
        attacker = make_unit("ally_001", x=0, y=0, position_x=0.0, position_y=0.0, attack_range=18.0, action_interval_ticks=20)
        state = make_state([attacker])
        events: List[BattleEvent] = []

        effect = ActionScheduleEffect(
            unit="ally_001",
            current_tick=10,
            next_action_tick=30,
            action_interval_ticks=20,
            reason="after_action",
        )
        action = build_basic_attack_action("ally_001", "enemy_001", 10, "test")
        emit_events_from_effects(state, action, [effect], 10, events)

        scheduled_events = [e for e in events if e.type == "action_scheduled"]
        self.assertEqual(1, len(scheduled_events))
        payload = scheduled_events[0].payload
        self.assertEqual("ally_001", payload["unit"])
        self.assertEqual(10, payload["current_tick"])
        self.assertEqual(30, payload["next_action_tick"])
        self.assertEqual(20, payload["action_interval_ticks"])
        self.assertEqual("after_action", payload["reason"])

    def test_models_are_json_safe(self):
        action = CombatAction(
            action_id="action_000001_ally_001_basic_attack_0001",
            unit_id="ally_001",
            action_type="basic_attack",
            target_id="enemy_001",
            tick=10,
            reason="spatial_engaged_target",
            skill_id=None,
            metadata={"target_reason": "current_target"},
        )
        action_result = ActionResult(
            ok=True,
            events=[BattleEvent(tick=10, event_id="evt_000001", type="damage", payload={"target": "enemy_001", "amount": 9})],
            reason="basic_attack_resolved",
            effects=[
                DamageEffect(source="ally_001", target="enemy_001", amount=9, reason="basic_attack"),
                CooldownEffect(source="ally_001", skill_id="fire_bolt", start_tick=10, ready_tick=30, cooldown_ticks=20),
                StatusApplyEffect(source="ally_001", target="ally_001", status_id="status_ally_001_buff_001", stat="atk", amount=5, expire_tick=None, reason="skill:fire_bolt"),
                DeathEffect(unit="enemy_001", reason="lethal_damage"),
                ActionScheduleEffect(unit="ally_001", current_tick=10, next_action_tick=30, action_interval_ticks=20, reason="after_action"),
            ],
        )

        json.dumps(asdict(action))
        json.dumps(asdict(action_result))

        self.assertTrue(action_result.ok)

    def test_demo_001_result_stable(self):
        state, events = run_basic_combat(self.bundle, "demo_001", 1001)
        self.assertEqual("ally", state.result.winner)
        self.assertEqual("enemy_eliminated", state.result.reason)
        self.assertGreater(state.result.end_tick, 0)
        self.assertTrue(state.finished)


if __name__ == "__main__":
    unittest.main()
