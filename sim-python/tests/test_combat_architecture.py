import json
import sys
import unittest
from dataclasses import asdict
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
from ikusa_sim.actions import (  # noqa: E402
    ActionResult,
    CombatAction,
    build_basic_attack_action,
    build_skill_action,
    resolve_combat_action,
    validate_combat_action,
)
from ikusa_sim.battle_session import (  # noqa: E402
    BattleSession,
    build_battle_snapshot,
    create_battle_session,
    initialize_battle_session,
    step_battle_session,
)
from ikusa_sim.combat_rules import apply_damage  # noqa: E402
from ikusa_sim.config_loader import load_config  # noqa: E402
from ikusa_sim.decisions import ActionDecision, IntentDecision, MovementDecision, SkillDecision  # noqa: E402
from ikusa_sim.events import BattleEvent  # noqa: E402
from ikusa_sim.report import build_battle_report_from_events  # noqa: E402
from ikusa_sim.runtime_models import BattleState, UnitState as RuntimeUnitState  # noqa: E402
from ikusa_sim.basic_combat import run_basic_combat  # noqa: E402
from ikusa_sim.spatial_combat import distance_between  # noqa: E402
from ikusa_sim.unit_fsm import get_unit_combat_state  # noqa: E402


class CombatArchitectureTests(unittest.TestCase):
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

    def test_unit_state_defaults_to_idle(self) -> None:
        unit = self.make_unit(instance_id="ally_001", side="ally")
        self.assertEqual("idle", unit.combat_state)
        self.assertEqual("hold", unit.movement_intent)

    def test_unit_spawn_payload_and_snapshot_include_combat_state(self) -> None:
        session = create_battle_session(self.bundle, "demo_001", 1001)

        events = initialize_battle_session(session)
        spawn_events = [event for event in events if event.type == "unit_spawn"]
        self.assertGreaterEqual(len(spawn_events), 2)
        self.assertEqual("idle", spawn_events[0].payload["unit"]["combat_state"])

        snapshot = build_battle_snapshot(session)
        json.dumps(snapshot)
        self.assertIn("combat_state", snapshot["units"][0])
        self.assertEqual("idle", snapshot["units"][0]["combat_state"])

    def test_moving_unit_sets_moving_to_engage(self) -> None:
        session, attacker, target = self.make_duel_session(
            attack_range=18.0,
            move_speed=24.0,
            start_distance=80.0,
            attacker_next_action_tick=1,
            attacker_action_interval_ticks=999,
            target_move_speed=0.0,
            target_next_action_tick=999,
            target_action_interval_ticks=999,
        )

        events = step_battle_session(session, ticks=5)
        event_types = [event.type for event in events]
        self.assertIn("target_acquired", event_types)
        self.assertIn("unit_move", event_types)
        self.assertEqual("moving_to_engage", get_unit_combat_state(attacker))
        self.assertEqual("moving_to_engage", attacker.combat_state)
        self.assertGreater(distance_between(attacker, target), 0.0)

    def test_in_range_unit_sets_engaged(self) -> None:
        session, attacker, _ = self.make_duel_session(
            attack_range=18.0,
            move_speed=24.0,
            start_distance=12.0,
            attacker_next_action_tick=999,
            attacker_action_interval_ticks=999,
            target_move_speed=0.0,
            target_next_action_tick=999,
            target_action_interval_ticks=999,
        )

        events = step_battle_session(session, ticks=1)
        event_types = {event.type for event in events}
        self.assertIn("enter_range", event_types)
        self.assertIn("engage_start", event_types)
        self.assertEqual("engaged", get_unit_combat_state(attacker))
        self.assertEqual("engaged", attacker.combat_state)

    def test_dead_unit_sets_dead(self) -> None:
        unit = self.make_unit(instance_id="ally_001", side="ally")
        died = apply_damage(unit, unit.hp, reason="test_lethal", source="enemy_001")
        self.assertTrue(died)
        self.assertFalse(unit.alive)
        self.assertEqual("dead", get_unit_combat_state(unit))
        self.assertEqual("dead", unit.combat_state)

    def test_decision_and_action_models_are_json_safe(self) -> None:
        intent = IntentDecision(unit_id="ally_001", intent="move_to_engage", reason="nearest_enemy", score=0.75, target_id="enemy_001")
        movement = MovementDecision(
            unit_id="ally_001",
            intent="move_to_attack_range",
            target_id="enemy_001",
            destination_x=128.0,
            destination_y=168.0,
            reason="move_to_attack_range",
            score=12.5,
        )
        skill = SkillDecision(
            unit_id="ally_001",
            skill_id="skill_fire",
            target_ids=["enemy_001"],
            reason="current_target",
            score=2.5,
            can_cast=True,
        )
        action_decision = ActionDecision(
            unit_id="ally_001",
            action_type="basic_attack",
            target_id="enemy_001",
            reason="current_target",
            score=7.0,
        )
        basic_action = build_basic_attack_action("ally_001", "enemy_001", 12, "current_target")
        skill_action = build_skill_action("ally_001", "skill_fire", "enemy_001", 12, "current_target")
        action_result = resolve_combat_action(basic_action)
        validation = validate_combat_action(skill_action)
        explicit_result = ActionResult(
            ok=True,
            events=[BattleEvent(tick=12, event_id="evt_000001", type="battle_start", payload={"battle_id": "demo_001"})],
            reason="validated",
        )

        for value in (intent, movement, skill, action_decision, basic_action, skill_action, action_result, validation, explicit_result):
            json.dumps(asdict(value))

        self.assertTrue(action_result.ok)
        self.assertTrue(validation.ok)

    def test_run_basic_combat_demo_result_stays_stable(self) -> None:
        state, events = run_basic_combat(self.bundle, "demo_001", 1001)
        self.assertEqual(12, len(state.units))
        self.assertGreater(len(events), 0)
        self.assertIsNotNone(state.result)
        self.assertEqual("ally", state.result.winner)
        self.assertEqual("enemy_eliminated", state.result.reason)
        self.assertEqual(341, state.result.end_tick)
        self.assertTrue(any(unit.combat_state == "dead" for unit in state.units if not unit.alive))

        report = build_battle_report_from_events(
            {
                "battle_id": state.battle_id,
                "seed": state.seed,
                "result": {
                    "winner": state.result.winner,
                    "reason": state.result.reason,
                    "end_tick": state.result.end_tick,
                },
            },
            [asdict(event) for event in events],
        )
        self.assertEqual("ally", report["winner"])
        self.assertEqual("enemy_eliminated", report["reason"])
        self.assertEqual(341, report["end_tick"])

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
        x: int = 0,
        y: int = 0,
        position_x: float = 0.0,
        position_y: float = 0.0,
        attack_range: float = 18.0,
        move_speed: float = 24.0,
        next_action_tick: int = 0,
        action_interval_ticks: int = 0,
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
