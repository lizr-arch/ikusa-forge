import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
SIM_DIR = REPO_ROOT / "sim-python"
TOOLS_DIR = REPO_ROOT / "tools"
for path in (SIM_DIR, TOOLS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from export_xlsx_to_json import export_tables  # noqa: E402
from ikusa_sim.battle_session import (  # noqa: E402
    BattleSession,
    build_battle_snapshot,
    create_battle_session,
    step_battle_session,
)
from ikusa_sim.events import event_to_dict  # noqa: E402
from ikusa_sim.runtime_models import BattleState, UnitState as RuntimeUnitState  # noqa: E402
from ikusa_sim.spatial_combat import (  # noqa: E402
    distance_between,
    in_attack_range,
    nearest_alive_enemy,
    select_engaged_target_decision,
)
from ikusa_sim.config_loader import load_config  # noqa: E402


class SpatialCombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._temp_dir = TemporaryDirectory()

        cls.generated_dir = Path(cls._temp_dir.name) / "generated"
        export_tables(REPO_ROOT / "config" / "source", cls.generated_dir)
        cls.bundle = load_config(cls.generated_dir)
        cls.sample_unit_def = next(iter(cls.bundle.units.values()))

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temp_dir.cleanup()

    def test_initial_positions_have_continuous_layout(self) -> None:
        session = create_battle_session(self.bundle, "demo_001", 1001)
        from ikusa_sim.battle_session import initialize_battle_session  # local import to keep the test focused

        initialize_battle_session(session)

        units = {unit.instance_id: unit for unit in session.state.units}
        self.assertEqual(12, len(units))
        self.assertTrue(all(isinstance(unit.position_x, float) for unit in units.values()))
        self.assertTrue(all(isinstance(unit.position_y, float) for unit in units.values()))

        for unit in units.values():
            expected_x = 80.0 + unit.x * 56.0
            expected_y = 80.0 + unit.y * 36.0 if unit.side == "enemy" else 320.0 + unit.y * 36.0
            self.assertEqual(expected_x, unit.position_x)
            self.assertEqual(expected_y, unit.position_y)

        ally_positions = {unit.position_y for unit in units.values() if unit.side == "ally"}
        enemy_positions = {unit.position_y for unit in units.values() if unit.side == "enemy"}
        self.assertTrue(ally_positions and enemy_positions)
        self.assertTrue(all(position > 200.0 for position in ally_positions))
        self.assertTrue(all(position < 200.0 for position in enemy_positions))

    def test_melee_out_of_range_moves_before_attacking(self) -> None:
        session, attacker, target = self.make_duel_session(
            attack_range=18.0,
            move_speed=24.0,
            start_distance=80.0,
            attacker_next_action_tick=1,
            attacker_action_interval_ticks=1,
            target_move_speed=0.0,
            target_next_action_tick=999,
            target_action_interval_ticks=999,
        )

        self.assertGreater(distance_between(attacker, target), attacker.attack_range)
        self.assertFalse(in_attack_range(attacker, target))
        self.assertIs(nearest_alive_enemy(attacker, session.state.units), target)

        events = step_battle_session(session, ticks=5)
        event_types = [event.type for event in events]

        self.assertIn("target_acquired", event_types)
        self.assertIn("unit_move", event_types)
        self.assertNotIn("attack", event_types)
        self.assertNotIn("damage", event_types)
        self.assertLess(distance_between(attacker, target), 80.0)

    def test_melee_enters_range_then_attacks(self) -> None:
        session, attacker, target = self.make_duel_session(
            attack_range=18.0,
            move_speed=24.0,
            start_distance=30.0,
            attacker_next_action_tick=1,
            attacker_action_interval_ticks=1,
            target_move_speed=0.0,
            target_next_action_tick=999,
            target_action_interval_ticks=999,
        )

        enter_seen = False
        engage_seen = False
        attack_seen = False
        damage_seen = False
        for _ in range(60):
            events = step_battle_session(session, ticks=1)
            event_types = {event.type for event in events}
            enter_seen = enter_seen or "enter_range" in event_types
            engage_seen = engage_seen or "engage_start" in event_types
            attack_seen = attack_seen or "attack" in event_types
            damage_seen = damage_seen or "damage" in event_types
            if attack_seen and damage_seen:
                break

        self.assertTrue(enter_seen)
        self.assertTrue(engage_seen)
        self.assertTrue(attack_seen)
        self.assertTrue(damage_seen)
        self.assertLessEqual(distance_between(attacker, target), attacker.attack_range + 0.001)
        decision = select_engaged_target_decision(attacker, session.state.units)
        self.assertEqual("spatial_engaged_target", decision.reason)
        self.assertEqual(target.instance_id, decision.target.instance_id)

    def test_ranged_behavior_attacks_from_further_out(self) -> None:
        melee_session, melee_attacker, melee_target = self.make_duel_session(
            attack_range=18.0,
            move_speed=24.0,
            start_distance=80.0,
            attacker_next_action_tick=1,
            attacker_action_interval_ticks=1,
            target_move_speed=0.0,
            target_next_action_tick=999,
            target_action_interval_ticks=999,
        )
        ranged_session, ranged_attacker, ranged_target = self.make_duel_session(
            attack_range=110.0,
            move_speed=18.0,
            start_distance=80.0,
            attacker_next_action_tick=1,
            attacker_action_interval_ticks=1,
            target_move_speed=0.0,
            target_next_action_tick=999,
            target_action_interval_ticks=999,
        )

        melee_events = step_battle_session(melee_session, ticks=5)
        ranged_events = step_battle_session(ranged_session, ticks=1)

        melee_types = [event.type for event in melee_events]
        ranged_types = [event.type for event in ranged_events]

        self.assertIn("unit_move", melee_types)
        self.assertNotIn("attack", melee_types)
        self.assertNotIn("damage", melee_types)
        self.assertNotIn("unit_move", ranged_types)
        self.assertIn("enter_range", ranged_types)
        self.assertIn("engage_start", ranged_types)
        self.assertIn("attack", ranged_types)
        self.assertIn("damage", ranged_types)

        self.assertLess(distance_between(melee_attacker, melee_target), 80.0)
        self.assertEqual(80.0, distance_between(ranged_attacker, ranged_target))

    def test_spatial_event_stream_is_deterministic(self) -> None:
        first_session, _, _ = self.make_duel_session(
            attack_range=18.0,
            move_speed=24.0,
            start_distance=40.0,
            attacker_next_action_tick=1,
            attacker_action_interval_ticks=1,
            target_move_speed=0.0,
            target_next_action_tick=999,
            target_action_interval_ticks=999,
            seed=777,
        )
        second_session, _, _ = self.make_duel_session(
            attack_range=18.0,
            move_speed=24.0,
            start_distance=40.0,
            attacker_next_action_tick=1,
            attacker_action_interval_ticks=1,
            target_move_speed=0.0,
            target_next_action_tick=999,
            target_action_interval_ticks=999,
            seed=777,
        )

        first_events = []
        second_events = []
        for _ in range(20):
            first_events.extend(step_battle_session(first_session, ticks=1))
            second_events.extend(step_battle_session(second_session, ticks=1))

        self.assertEqual(
            [event_to_dict(event) for event in first_session.events],
            [event_to_dict(event) for event in second_session.events],
        )
        self.assertEqual(
            [event_to_dict(event) for event in first_events],
            [event_to_dict(event) for event in second_events],
        )

    def test_snapshot_includes_spatial_fields_and_position_changes(self) -> None:
        session, attacker, target = self.make_duel_session(
            attack_range=18.0,
            move_speed=24.0,
            start_distance=80.0,
            attacker_next_action_tick=1,
            attacker_action_interval_ticks=1,
            target_move_speed=0.0,
            target_next_action_tick=999,
            target_action_interval_ticks=999,
        )

        before = build_battle_snapshot(session)
        json.dumps(before)
        before_positions = {unit["instance_id"]: (unit["position_x"], unit["position_y"]) for unit in before["units"]}

        for _ in range(5):
            step_battle_session(session, ticks=1)

        after = build_battle_snapshot(session)
        json.dumps(after)

        self.assertEqual("battle_snapshot.v0.1", before["schema_version"])
        self.assertEqual("battle_snapshot.v0.1", after["schema_version"])
        self.assertTrue(all(field in before["units"][0] for field in [
            "position_x",
            "position_y",
            "velocity_x",
            "velocity_y",
            "attack_range",
            "engaged_target",
            "movement_intent",
        ]))
        after_positions = {unit["instance_id"]: (unit["position_x"], unit["position_y"]) for unit in after["units"]}
        self.assertTrue(any(after_positions[unit_id] != before_positions[unit_id] for unit_id in before_positions))

        attacker_snapshot = next(unit for unit in after["units"] if unit["instance_id"] == attacker.instance_id)
        target_snapshot = next(unit for unit in after["units"] if unit["instance_id"] == target.instance_id)
        self.assertIsInstance(attacker_snapshot["position_x"], float)
        self.assertIsInstance(target_snapshot["position_y"], float)

    def make_duel_session(
        self,
        *,
        attack_range: float,
        move_speed: float,
        start_distance: float,
        attacker_next_action_tick: int,
        attacker_action_interval_ticks: int,
        target_move_speed: float,
        target_next_action_tick: int,
        target_action_interval_ticks: int,
        seed: int = 1001,
    ) -> Tuple[BattleSession, RuntimeUnitState, RuntimeUnitState]:
        attacker = self.make_unit(
            instance_id="ally_001",
            side="ally",
            x=0,
            y=0,
            position_x=0.0,
            position_y=0.0,
            attack_range=attack_range,
            move_speed=move_speed,
            next_action_tick=attacker_next_action_tick,
            action_interval_ticks=attacker_action_interval_ticks,
        )
        target = self.make_unit(
            instance_id="enemy_001",
            side="enemy",
            x=1,
            y=0,
            position_x=start_distance,
            position_y=0.0,
            attack_range=18.0,
            move_speed=target_move_speed,
            next_action_tick=target_next_action_tick,
            action_interval_ticks=target_action_interval_ticks,
        )
        state = BattleState(
            battle_id="spatial_test",
            seed=seed,
            tick_rate=10,
            max_ticks=200,
            current_tick=0,
            units=[attacker, target],
            finished=False,
            result=None,
            _next_event_number=1,
        )
        session = BattleSession(
            config=self.bundle,
            state=state,
            battle_id="spatial_test",
            seed=seed,
            initialized=True,
            finished=False,
            current_tick=0,
            events=[],
            event_cursor=0,
            max_ticks=state.max_ticks,
        )
        return session, attacker, target

    def make_unit(
        self,
        *,
        instance_id: str,
        side: str,
        x: int,
        y: int,
        position_x: float,
        position_y: float,
        attack_range: float,
        move_speed: float,
        next_action_tick: int,
        action_interval_ticks: int,
    ) -> RuntimeUnitState:
        unit_def = self.sample_unit_def
        return RuntimeUnitState(
            instance_id=instance_id,
            side=side,
            unit_def_id=unit_def.id,
            x=x,
            y=y,
            role="front",
            name=unit_def.name,
            tags=list(unit_def.tags),
            base_hp=5000,
            base_atk=20,
            base_defense=10,
            base_range=1,
            base_attack_interval=1.0,
            weapon_slots=[],
            skill_ids=[],
            hp=5000,
            alive=True,
            formation_id="",
            next_action_tick=next_action_tick,
            action_interval_ticks=action_interval_ticks,
            guard_value=0,
            position_x=position_x,
            position_y=position_y,
            radius=8.0,
            move_speed=move_speed,
            attack_range=attack_range,
            engagement_range=attack_range + 4.0 if attack_range < 100 else attack_range,
            engaged_target=None,
            movement_intent="hold",
        )


if __name__ == "__main__":
    unittest.main()
