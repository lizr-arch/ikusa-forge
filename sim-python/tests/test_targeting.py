import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from ikusa_sim.runtime_models import UnitState  # noqa: E402
from ikusa_sim.targeting import select_target  # noqa: E402


def make_unit(instance_id, side, x, y, attack_range=1, hp=100, base_hp=100):
    return UnitState(
        instance_id=instance_id,
        side=side,
        unit_def_id=instance_id,
        x=x,
        y=y,
        role="test",
        name=instance_id,
        tags=[],
        base_hp=base_hp,
        base_atk=10,
        base_defense=0,
        base_range=attack_range,
        base_attack_interval=1.0,
        weapon_slots=[],
        skill_ids=[],
        hp=hp,
        alive=True,
    )


class TargetingTests(unittest.TestCase):
    def test_range_one_only_targets_front_exposure_layer(self):
        attacker = make_unit("ally_001", "ally", 2, 0, attack_range=1)
        front = make_unit("enemy_front", "enemy", 0, 0)
        back_same_column = make_unit("enemy_back", "enemy", 2, 2)

        target = select_target(attacker, [attacker, front, back_same_column])

        self.assertEqual("enemy_front", target.instance_id)

    def test_range_three_can_target_backline(self):
        attacker = make_unit("ally_001", "ally", 2, 0, attack_range=3)
        front = make_unit("enemy_front", "enemy", 0, 0)
        back_same_column = make_unit("enemy_back", "enemy", 2, 2)

        target = select_target(attacker, [attacker, front, back_same_column])

        self.assertEqual("enemy_back", target.instance_id)

    def test_same_column_target_is_preferred(self):
        attacker = make_unit("ally_001", "ally", 1, 0, attack_range=1)
        same_column = make_unit("enemy_same", "enemy", 1, 0)
        adjacent = make_unit("enemy_adjacent", "enemy", 2, 0, hp=10)

        target = select_target(attacker, [attacker, adjacent, same_column])

        self.assertEqual("enemy_same", target.instance_id)

    def test_low_hp_adds_priority(self):
        attacker = make_unit("ally_001", "ally", 0, 0, attack_range=1)
        healthy = make_unit("enemy_healthy", "enemy", 3, 0, hp=100)
        wounded = make_unit("enemy_wounded", "enemy", 3, 0, hp=20)

        target = select_target(attacker, [attacker, healthy, wounded])

        self.assertEqual("enemy_wounded", target.instance_id)

    def test_tie_breaks_by_instance_id(self):
        attacker = make_unit("ally_001", "ally", 0, 0, attack_range=1)
        later = make_unit("enemy_002", "enemy", 3, 0)
        earlier = make_unit("enemy_001", "enemy", 3, 0)

        target = select_target(attacker, [attacker, later, earlier])

        self.assertEqual("enemy_001", target.instance_id)


if __name__ == "__main__":
    unittest.main()
