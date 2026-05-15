import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from ikusa_sim.combat_rules import (  # noqa: E402
    apply_damage,
    attack_interval_to_ticks,
    calculate_basic_damage,
    calculate_skill_damage,
)
from ikusa_sim.models import SkillDef  # noqa: E402
from ikusa_sim.runtime_models import UnitState  # noqa: E402


def make_unit(instance_id, atk=10, defense=0, hp=20):
    return UnitState(
        instance_id=instance_id,
        side="ally",
        unit_def_id=instance_id,
        x=0,
        y=0,
        role="test",
        name=instance_id,
        tags=[],
        base_hp=hp,
        base_atk=atk,
        base_defense=defense,
        base_range=1,
        base_attack_interval=1.0,
        weapon_slots=[],
        skill_ids=[],
        hp=hp,
        alive=True,
    )


class CombatRuleTests(unittest.TestCase):
    def test_attack_interval_converts_to_ticks(self):
        self.assertEqual(24, attack_interval_to_ticks(1.2, 20))
        self.assertEqual(1, attack_interval_to_ticks(0.0, 20))

    def test_basic_damage_uses_current_atk_minus_current_defense(self):
        attacker = make_unit("attacker", atk=14)
        defender = make_unit("defender", defense=6)
        attacker.atk = 18
        defender.defense = 5

        self.assertEqual(13, calculate_basic_damage(attacker, defender))

    def test_basic_damage_has_minimum_one(self):
        attacker = make_unit("attacker", atk=3)
        defender = make_unit("defender", defense=10)

        self.assertEqual(1, calculate_basic_damage(attacker, defender))

    def test_guard_value_reduces_damage_with_minimum_one(self):
        attacker = make_unit("attacker", atk=14)
        defender = make_unit("defender", defense=6)
        defender.guard_value = 20

        self.assertEqual(1, calculate_basic_damage(attacker, defender))

    def test_skill_damage_uses_current_stats_and_effect_value(self):
        attacker = make_unit("attacker", atk=14)
        defender = make_unit("defender", defense=6)
        skill = SkillDef(
            id="katana_slash",
            name="Katana Slash",
            trigger="on_attack",
            target_rule="current_target",
            cooldown=1.0,
            effect_type="damage",
            effect_value=16,
            tags=[],
        )
        attacker.atk = 18
        defender.defense = 5

        self.assertEqual(29, calculate_skill_damage(attacker, defender, skill))

    def test_apply_damage_reduces_hp_without_death(self):
        defender = make_unit("defender", hp=20)

        died = apply_damage(defender, 5)

        self.assertFalse(died)
        self.assertEqual(15, defender.hp)
        self.assertTrue(defender.alive)

    def test_apply_damage_marks_death_at_zero_hp(self):
        defender = make_unit("defender", hp=20)

        died = apply_damage(defender, 25)

        self.assertTrue(died)
        self.assertEqual(0, defender.hp)
        self.assertFalse(defender.alive)


if __name__ == "__main__":
    unittest.main()
