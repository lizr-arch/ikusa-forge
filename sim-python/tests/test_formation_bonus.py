import sys
import unittest
from typing import List
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from ikusa_sim.events import BattleEvent
from ikusa_sim.formation_bonus import apply_formation_bonuses
from ikusa_sim.runtime_models import BattleState, UnitState


def _make_unit(*, instance_id: str, formation_id: str, role: str, atk: int = 10) -> UnitState:
    return UnitState(
        instance_id=instance_id,
        side="ally",
        unit_def_id="unit_def",
        x=0,
        y=0,
        role=role,
        name=instance_id,
        tags=[],
        base_hp=120,
        base_atk=atk,
        base_defense=5,
        base_range=1,
        base_attack_interval=1.0,
        weapon_slots=[],
        skill_ids=[],
        hp=120,
        alive=True,
        formation_id=formation_id,
    )


def _make_state(units: List[UnitState]) -> BattleState:
    return BattleState(
        battle_id="bonus_unit_test",
        seed=1001,
        tick_rate=20,
        max_ticks=100,
        current_tick=0,
        units=list(units),
        finished=False,
        result=None,
        _next_event_number=1,
    )


class FormationBonusTests(unittest.TestCase):
    def test_fish_scale_grants_atk_to_vanguard_and_center(self) -> None:
        state = _make_state(
            [
                _make_unit(instance_id="ally_001", formation_id="fish_scale", role="vanguard", atk=10),
                _make_unit(instance_id="ally_002", formation_id="fish_scale", role="center", atk=12),
                _make_unit(instance_id="ally_003", formation_id="fish_scale", role="support", atk=8),
            ]
        )
        events: List[BattleEvent] = []

        apply_formation_bonuses(state, events)

        self.assertEqual(13, state.units[0].atk)
        self.assertEqual(15, state.units[1].atk)
        self.assertEqual(8, state.units[2].atk)
        self.assertEqual(2, len(events))
        self.assertTrue(all(event.type == "stat_modifier" for event in events))
        self.assertEqual({"ally_001", "ally_002"}, {event.payload["target"] for event in events})
        self.assertTrue(all(event.payload["source_type"] == "formation" for event in events))
        self.assertTrue(all(event.payload["stat"] == "atk" for event in events))

    def test_crane_wing_targets_flank_and_support(self) -> None:
        state = _make_state(
            [
                _make_unit(instance_id="ally_001", formation_id="crane_wing", role="left_flank", atk=10),
                _make_unit(instance_id="ally_002", formation_id="crane_wing", role="right_flank", atk=10),
                _make_unit(instance_id="ally_003", formation_id="crane_wing", role="support", atk=10),
            ]
        )
        events: List[BattleEvent] = []

        apply_formation_bonuses(state, events)

        self.assertEqual(12, state.units[0].atk)
        self.assertEqual(12, state.units[1].atk)
        self.assertEqual(11, state.units[2].atk)
        self.assertEqual(3, len(events))

    def test_goose_line_applies_backline_defense_bonus(self) -> None:
        state = _make_state(
            [
                _make_unit(instance_id="ally_001", formation_id="goose_line", role="backline", atk=10),
                _make_unit(instance_id="ally_002", formation_id="goose_line", role="backline", atk=10),
                _make_unit(instance_id="ally_003", formation_id="goose_line", role="vanguard", atk=10),
            ]
        )
        base_defenses = [unit.defense for unit in state.units]
        events: List[BattleEvent] = []

        apply_formation_bonuses(state, events)

        self.assertEqual(base_defenses[0] + 2, state.units[0].defense)
        self.assertEqual(base_defenses[1] + 2, state.units[1].defense)
        self.assertEqual(base_defenses[2], state.units[2].defense)
        self.assertEqual(2, len(events))
        self.assertEqual(["evt_000001", "evt_000002"], [event.event_id for event in events])

    def test_unknown_formation_id_does_not_change_units(self) -> None:
        state = _make_state([_make_unit(instance_id="ally_001", formation_id="unknown", role="vanguard")])
        events: List[BattleEvent] = []

        apply_formation_bonuses(state, events)

        self.assertEqual(10, state.units[0].atk)
        self.assertEqual([], events)


if __name__ == "__main__":
    unittest.main()
