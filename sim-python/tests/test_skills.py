import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from ikusa_sim.models import ConfigBundle, Constants, SkillDef  # noqa: E402
from ikusa_sim.runtime_models import BattleState, UnitState  # noqa: E402
from ikusa_sim.skills import (  # noqa: E402
    get_ready_skills,
    mark_skill_used,
    try_use_on_ally_attacked_skills,
    try_use_on_attack_skill,
    try_use_on_attacked_skills,
    try_use_on_battle_start_skills,
)


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
    )


class SkillTests(unittest.TestCase):
    def test_skill_cooldown_blocks_until_ready_tick(self):
        skill = make_skill("katana_slash", "on_attack", cooldown=2.0)
        config = make_config(skill)
        unit = make_unit("ally_001", skill_ids=["katana_slash"])

        self.assertEqual([skill], get_ready_skills(unit, config, "on_attack", 0))

        ready_tick = mark_skill_used(unit, skill, tick=0, tick_rate=20)

        self.assertEqual(40, ready_tick)
        self.assertEqual([], get_ready_skills(unit, config, "on_attack", 39))
        self.assertEqual([skill], get_ready_skills(unit, config, "on_attack", 40))

    def test_shield_guard_triggers_on_battle_start(self):
        skill = make_skill(
            "shield_guard",
            "on_battle_start",
            target_rule="self",
            effect_type="guard",
            effect_value=12,
        )
        config = make_config(skill)
        shield = make_unit("ally_001", skill_ids=["shield_guard"])
        state = make_state([shield])
        events = []

        try_use_on_battle_start_skills(state, config, events)

        self.assertEqual(12, shield.guard_value)
        self.assertEqual(["skill_trigger", "status_apply", "skill_cooldown"], [event.type for event in events])
        self.assertEqual("shield_guard", events[0].payload["skill"])
        self.assertEqual(["ally_001"], events[0].payload["targets"])
        self.assertEqual("skill:shield_guard", events[1].payload["reason"])
        self.assertEqual("guard_value", events[1].payload["stat"])
        self.assertEqual("self", events[1].payload["target_reason"])
        self.assertEqual(1, len(shield.statuses))
        self.assertEqual(20, events[2].payload["ready_tick"])

    def test_banner_rally_buffs_adjacent_allies(self):
        skill = make_skill(
            "banner_rally",
            "on_battle_start",
            target_rule="adjacent_allies",
            effect_type="buff",
            effect_value=8,
        )
        config = make_config(skill)
        banner = make_unit("ally_banner", x=0, y=0, skill_ids=["banner_rally"])
        adjacent = make_unit("ally_adjacent", x=1, y=1, atk=10)
        far = make_unit("ally_far", x=3, y=2, atk=10)
        enemy = make_unit("enemy_001", side="enemy", x=1, y=0, atk=10)
        state = make_state([banner, adjacent, far, enemy])
        events = []

        try_use_on_battle_start_skills(state, config, events)

        self.assertEqual(18, adjacent.atk)
        self.assertEqual(10, far.atk)
        self.assertEqual(10, enemy.atk)
        self.assertEqual(["ally_adjacent"], events[0].payload["targets"])
        self.assertEqual(["skill_trigger", "status_apply", "skill_cooldown"], [event.type for event in events])
        self.assertEqual("atk", events[1].payload["stat"])
        self.assertEqual(8, events[1].payload["amount"])
        self.assertEqual("adjacent_allies", events[1].payload["target_reason"])
        self.assertEqual(1, len(adjacent.statuses))

    def test_on_attack_skill_triggers_and_deals_skill_damage(self):
        skill = make_skill("katana_slash", "on_attack", effect_value=16)
        config = make_config(skill)
        attacker = make_unit("ally_001", atk=18, skill_ids=["katana_slash"])
        target = make_unit("enemy_001", side="enemy", hp=40, defense=5)
        state = make_state([attacker, target])
        events = []

        result = try_use_on_attack_skill(attacker, target, state, config, 0, events)

        self.assertTrue(result.used)
        self.assertEqual([target], result.damaged_targets)
        self.assertEqual(["skill_trigger", "damage", "skill_cooldown"], [event.type for event in events])
        self.assertEqual("skill:katana_slash", events[1].payload["reason"])
        self.assertEqual("katana_slash", events[2].payload["skill"])
        self.assertEqual(11, target.hp)

    def test_brace_counter_reacts_without_recursive_reaction(self):
        skill = make_skill(
            "brace_counter",
            "on_attacked",
            target_rule="attacker",
            effect_type="counter_damage",
            effect_value=18,
        )
        config = make_config(skill)
        attacker = make_unit("ally_001", atk=18, defense=5, skill_ids=["brace_counter"])
        defender = make_unit("enemy_001", side="enemy", atk=14, skill_ids=["brace_counter"])
        state = make_state([attacker, defender])
        events = []

        try_use_on_attacked_skills(attacker, defender, state, config, 0, events)

        self.assertEqual(["skill_trigger", "damage", "skill_cooldown"], [event.type for event in events])
        self.assertEqual("brace_counter", events[0].payload["skill"])
        self.assertEqual("skill:brace_counter", events[1].payload["reason"])

    def test_intercept_reacts_to_ally_attacked(self):
        skill = make_skill(
            "intercept",
            "on_ally_attacked",
            target_rule="attacker",
            effect_type="intercept",
            effect_value=10,
        )
        config = make_config(skill)
        attacker = make_unit("enemy_001", side="enemy", hp=40, defense=5)
        defender = make_unit("ally_002")
        protector = make_unit("ally_001", atk=12, skill_ids=["intercept"])
        state = make_state([protector, defender, attacker])
        events = []

        try_use_on_ally_attacked_skills(attacker, defender, state, config, 0, events)

        self.assertEqual(["skill_trigger", "damage", "skill_cooldown"], [event.type for event in events])
        self.assertEqual("intercept", events[0].payload["skill"])
        self.assertEqual("skill:intercept", events[1].payload["reason"])
        self.assertLess(attacker.hp, 40)


if __name__ == "__main__":
    unittest.main()
