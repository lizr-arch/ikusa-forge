import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from dataclasses import asdict

REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
TOOLS_DIR = REPO_ROOT / "tools"
for path in (SIM_DIR, TOOLS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from export_xlsx_to_json import export_tables  # noqa: E402
from ikusa_sim.action_pipeline import build_skill_action as make_skill_action
from ikusa_sim.action_pipeline import run_combat_action
from ikusa_sim.battle_session import _run_tick
from ikusa_sim.config_loader import load_config  # noqa: E402
from ikusa_sim.effect_models import StatusApplyEffect, StatusExpireEffect
from ikusa_sim.models import ConfigBundle, Constants, SkillDef  # noqa: F401
from ikusa_sim.runtime_models import BattleState, StatusEffect, UnitState
from ikusa_sim import status_system
from ikusa_sim.skills import try_use_on_battle_start_skills


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
    )


class PipelineHardeningTests(unittest.TestCase):
    def export_sample_config(self):
        temp_dir = TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)

        output_dir = Path(temp_dir.name) / "generated"
        export_tables(REPO_ROOT / "config" / "source", output_dir)
        return output_dir

    def run_demo(self):
        from ikusa_sim.basic_combat import run_basic_combat

        bundle = load_config(self.export_sample_config())
        return run_basic_combat(bundle, "demo_001", 1001)

    def test_action_scheduled_from_pipeline_flow(self):
        attacker = make_unit(
            "ally_001",
            x=0,
            y=0,
            position_x=0.0,
            position_y=0.0,
            next_action_tick=1,
        )
        target = make_unit(
            "enemy_001",
            side="enemy",
            x=0,
            y=0,
            position_x=10.0,
            position_y=0.0,
            hp=40,
            next_action_tick=999,
        )
        state = make_state([attacker, target])
        events: List = []
        config = make_config()

        result = _run_tick(state, config, events, tick=1)
        self.assertIsNone(result)

        scheduled = [event for event in events if event.type == "action_scheduled"]
        self.assertEqual(1, len(scheduled))
        payload = scheduled[0].payload
        self.assertEqual("ally_001", payload["unit"])
        self.assertEqual(1, payload["current_tick"])
        self.assertEqual(21, payload["next_action_tick"])
        self.assertEqual(20, payload["action_interval_ticks"])
        self.assertEqual("after_action", payload["reason"])
        self.assertEqual(1 + payload["action_interval_ticks"], payload["next_action_tick"])

    def test_skill_cooldown_via_pipeline(self):
        skill = make_skill("blade_flare", trigger="on_attack", target_rule="current_target", cooldown=1.0, effect_type="damage", effect_value=16)
        attacker = make_unit(
            "ally_001",
            x=0,
            y=0,
            position_x=0.0,
            position_y=0.0,
            hp=100,
            skill_ids=["blade_flare"],
        )
        target = make_unit(
            "enemy_001",
            side="enemy",
            x=0,
            y=0,
            position_x=5.0,
            position_y=0.0,
            hp=80,
        )
        config = make_config(skill)
        state = make_state([attacker, target])
        events: List = []

        action = make_skill_action(state, attacker, skill, [target], tick=5)
        action.metadata["target_reason"] = "current_target"
        action.metadata["effect_type"] = "damage"
        result = run_combat_action(state, action, 5, events)

        self.assertTrue(result.ok)
        self.assertEqual(20, attacker.skill_cooldowns["blade_flare"])
        skill_events = [event for event in events if event.type == "skill_cooldown"]
        self.assertEqual(1, len(skill_events))
        payload = skill_events[0].payload
        self.assertEqual("blade_flare", payload["skill"])
        self.assertEqual(state.current_tick, payload["start_tick"])
        self.assertEqual(20, payload["ready_tick"])

    def test_battle_start_skill_uses_pipeline(self):
        state = make_state([make_unit("ally_001", skill_ids=["shield_guard"])])
        config = make_config(make_skill("shield_guard", trigger="on_battle_start", target_rule="self", cooldown=6.0, effect_type="guard", effect_value=12))
        events: List = []

        try_use_on_battle_start_skills(state, config, events)

        trigger_events = [event for event in events if event.type == "skill_trigger"]
        apply_events = [event for event in events if event.type == "status_apply"]
        cooldown_events = [event for event in events if event.type == "skill_cooldown"]

        self.assertEqual(1, len(trigger_events))
        self.assertEqual(1, len(apply_events))
        self.assertEqual(1, len(cooldown_events))
        self.assertEqual("shield_guard", trigger_events[0].payload["skill"])
        self.assertEqual("ally_001", cooldown_events[0].payload["source"])
        self.assertIn("skill:shield_guard", apply_events[0].payload["reason"])
        self.assertEqual(120, state.units[0].skill_cooldowns["shield_guard"])

    def test_reactive_skill_paths_use_pipeline(self):
        config = make_config(
            make_skill("brace_counter", trigger="on_attacked", target_rule="attacker", cooldown=3.0, effect_type="counter_damage", effect_value=18),
            make_skill("intercept", trigger="on_ally_attacked", target_rule="attacker", cooldown=4.0, effect_type="intercept", effect_value=10),
        )
        attacker = make_unit("enemy_001", side="enemy", x=0, y=0, position_x=0.0, position_y=0.0, hp=100, next_action_tick=1)
        defender = make_unit("ally_001", side="ally", x=0, y=0, position_x=5.0, position_y=0.0, hp=100, skill_ids=["brace_counter"])
        ally_support = make_unit("ally_support", side="ally", x=0, y=0, position_x=10.0, position_y=0.0, hp=80, skill_ids=["intercept"])
        events: List = []

        state = make_state([attacker, defender, ally_support])
        _run_tick(state, config, events, tick=1)

        trigger_events = [event for event in events if event.type == "skill_trigger"]
        skill_ids = {event.payload.get("skill") for event in trigger_events}
        self.assertIn("brace_counter", skill_ids)
        self.assertIn("intercept", skill_ids)
        self.assertIn("ally_support", [event.payload.get("source") for event in trigger_events if event.payload.get("skill") == "intercept"])

    def test_status_expire_effect_lifecycle(self):
        state = make_state([make_unit("ally_001", hp=60, atk=12)])
        target = state.units[0]
        status_effect = StatusApplyEffect(
            source="source_001",
            target="ally_001",
            status_id="status_ally_001_guard_001",
            stat="guard_value",
            amount=5,
            expire_tick=3,
            reason="skill:shield_guard",
        )
        status_system.apply_status_effect(target, status_effect, tick=0)

        self.assertEqual(5, target.guard_value)
        self.assertEqual(1, len(target.statuses))
        self.assertEqual(5, target.guard_value)

        expired_effects = status_system.build_status_expire_effects(state, tick=3)
        self.assertEqual(1, len(expired_effects))
        self.assertIsInstance(expired_effects[0], StatusExpireEffect)

        for effect in expired_effects:
            status_system.apply_status_expire_effect(state, effect)

        self.assertEqual(0, target.guard_value)
        self.assertEqual(0, len(target.statuses))

        payload = status_system.emit_status_expire_event(3, expired_effects[0])
        json.dumps(payload)
        self.assertEqual("status_expire", payload["type"])
        self.assertEqual("status_ally_001_guard_001", payload["payload"]["status_id"])

    def test_status_without_expire_never_expired(self):
        state = make_state([make_unit("ally_001", hp=60, atk=12)])
        target = state.units[0]
        target.statuses.append(
            StatusEffect(
                id="status_perm",
                source="source_001",
                source_type="skill",
                target="ally_001",
                stat="atk",
                amount=7,
                start_tick=1,
                expire_tick=None,
                reason="skill:eternal",
            )
        )
        target.atk += 7

        expired_effects = status_system.build_status_expire_effects(state, tick=3)
        self.assertEqual(0, len(expired_effects))
        self.assertEqual(19, target.atk)

    def test_status_expire_effect_is_json_safe(self):
        effect = StatusExpireEffect(
            status_id="status_expire_001",
            target="ally_001",
            stat="atk",
            amount=5,
            reason="status_expired:status_expire_001",
        )

        json.dumps(asdict(effect))

    def test_demo_001_stable_with_pipeline_hardening(self):
        state, events = self.run_demo()
        self.assertEqual("ally", state.result.winner)
        self.assertEqual("enemy_eliminated", state.result.reason)
        self.assertIsNotNone(state.result.end_tick)
        self.assertTrue(state.finished)
        # Keep event contract stable for hardening checks
        event_types = [event.type for event in events]
        self.assertIn("action_scheduled", event_types)
        self.assertIn("skill_trigger", event_types)
        self.assertIn("status_apply", event_types)
        self.assertIn("skill_cooldown", event_types)
        self.assertIn("battle_end", event_types)


if __name__ == "__main__":
    unittest.main()
