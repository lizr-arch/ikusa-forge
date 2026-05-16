import sys
import unittest
from typing import List, Dict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
for path in (SIM_DIR,):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from ikusa_sim.events import BattleEvent
from ikusa_sim.models import ConfigBundle, Constants, SynergyDef
from ikusa_sim.runtime_models import BattleState, UnitState
from ikusa_sim.synergy import apply_synergies


def _make_unit(*, instance_id: str, side: str, role: str, tags: List[str], atk: int = 10) -> UnitState:
    return UnitState(
        instance_id=instance_id,
        side=side,
        unit_def_id="unit_def",
        x=0,
        y=0,
        role=role,
        name=instance_id,
        tags=tags,
        base_hp=120,
        base_atk=atk,
        base_defense=5,
        base_range=1,
        base_attack_interval=1.0,
        weapon_slots=[],
        skill_ids=[],
        hp=120,
        alive=True,
    )


def _make_state(units: List[UnitState]) -> BattleState:
    return BattleState(
        battle_id="synergy_unit_test",
        seed=1001,
        tick_rate=20,
        max_ticks=120,
        current_tick=0,
        units=list(units),
        finished=False,
        result=None,
        _next_event_number=1,
    )


def _make_config(*, synergy_id: str, thresholds: Dict[str, Dict[str, int]]) -> ConfigBundle:
    return ConfigBundle(
        constants=Constants(
            tick_rate=20,
            max_ticks=120,
            board_rows=3,
            board_cols=4,
            default_seed=1001,
        ),
        units={},
        weapons={},
        skills={},
        formations={},
        synergies={
            synergy_id: SynergyDef(
                id=synergy_id,
                name=synergy_id,
                required_tags=[],
                thresholds=thresholds,
                scope="matching_units",
            )
        },
        encounters={},
    )


class SynergyTests(unittest.TestCase):
    def test_spear_wall_applies_ally_and_enemy_by_side(self) -> None:
        state = _make_state(
            [
                _make_unit(instance_id="ally_001", side="ally", role="front", tags=["spear"]),
                _make_unit(instance_id="ally_002", side="ally", role="front", tags=["spear"]),
                _make_unit(instance_id="enemy_001", side="enemy", role="front", tags=["spear"]),
            ]
        )
        config = _make_config(
            synergy_id="spear_wall",
            thresholds={"2": {"atk": 2}},
        )
        events: List[BattleEvent] = []

        apply_synergies(state, config, events)

        self.assertEqual(12, state.units[0].atk)
        self.assertEqual(12, state.units[1].atk)
        self.assertEqual(10, state.units[2].atk)
        self.assertEqual(2, len(events))
        self.assertTrue(all(event.payload["source_type"] == "synergy" for event in events))
        self.assertEqual({"ally_001", "ally_002"}, {event.payload["target"] for event in events})

    def test_arrow_volley_threshold_not_reached_no_modifier(self) -> None:
        state = _make_state(
            [
                _make_unit(instance_id="ally_001", side="ally", role="front", tags=["bow"]),
            ]
        )
        config = _make_config(
            synergy_id="arrow_volley",
            thresholds={"2": {"atk": 2}},
        )
        events: List[BattleEvent] = []

        apply_synergies(state, config, events)

        self.assertEqual(10, state.units[0].atk)
        self.assertEqual([], events)

    def test_mixed_arms_require_side_local_tags(self) -> None:
        config = _make_config(
            synergy_id="mixed_arms",
            thresholds={"2": {"defense": 1}},
        )
        state = _make_state(
            [
                _make_unit(instance_id="ally_001", side="ally", role="front", tags=["spear"]),
                _make_unit(instance_id="ally_002", side="ally", role="front", tags=["bow"]),
                _make_unit(instance_id="ally_003", side="ally", role="front", tags=["katana"]),
                _make_unit(instance_id="ally_004", side="ally", role="front", tags=["support"]),
                _make_unit(instance_id="enemy_001", side="enemy", role="front", tags=["spear"]),
                _make_unit(instance_id="enemy_002", side="enemy", role="front", tags=["bow"]),
                _make_unit(instance_id="enemy_003", side="enemy", role="front", tags=["support"]),
            ]
        )
        events: List[BattleEvent] = []

        apply_synergies(state, config, events)

        self.assertEqual(4, len(events))
        self.assertEqual(4, len([event for event in events if event.type == "stat_modifier"]))
        # Only ally side owns all three required tags and can trigger mixed_arms.
        self.assertEqual(
            4,
            len({event.payload["target"] for event in events if event.payload.get("target", "").startswith("ally_")}),
        )
        self.assertTrue(all(event.payload["source"] == "synergy:mixed_arms" for event in events))

    def test_event_id_is_deterministic_and_stable(self) -> None:
        state = _make_state(
            [
                _make_unit(instance_id="ally_002", side="ally", role="front", tags=["spear"]),
                _make_unit(instance_id="ally_001", side="ally", role="front", tags=["spear"]),
            ]
        )
        config = _make_config(
            synergy_id="spear_wall",
            thresholds={"2": {"atk": 2}},
        )
        events: List[BattleEvent] = []

        apply_synergies(state, config, events)

        self.assertEqual(["evt_000001", "evt_000002"], [event.event_id for event in events])


if __name__ == "__main__":
    unittest.main()
