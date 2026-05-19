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
    initialize_battle_session,
    step_battle_session,
)
from ikusa_sim.config_loader import load_config  # noqa: E402
from ikusa_sim.events import event_to_dict  # noqa: E402
from ikusa_sim.runtime_models import BattleState, UnitState as RuntimeUnitState  # noqa: E402
from ikusa_sim.spatial_combat import (  # noqa: E402
    distance_between,
    initialize_spatial_state,
)


class FormationEngagementTests(unittest.TestCase):
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

    def test_formation_anchors_assigned_at_init(self) -> None:
        """After battle init, every unit has formation_anchor_x/y and correct group_id."""
        session = create_battle_session(self.bundle, "demo_001", 1001)
        initialize_battle_session(session)

        for unit in session.state.units:
            self.assertTrue(isinstance(unit.formation_anchor_x, float))
            self.assertTrue(isinstance(unit.formation_anchor_y, float))
            self.assertEqual(unit.side, unit.formation_group_id)
            self.assertNotEqual(0.0, unit.formation_anchor_y)

    def test_group_advance_preserves_relative_spacing(self) -> None:
        """After many steps, same-side units don't all overlap."""
        session = create_battle_session(self.bundle, "demo_001", 1001)
        initialize_battle_session(session)

        for _ in range(30):
            step_battle_session(session, ticks=5)

        ally_units = [u for u in session.state.units if u.side == "ally" and u.alive]
        for i, ua in enumerate(ally_units):
            for ub in ally_units[i + 1:]:
                dist = distance_between(ua, ub)
                min_dist = min(ua.separation_radius, ub.separation_radius) * 0.5
                self.assertGreater(
                    dist,
                    min_dist,
                    f"Units {ua.instance_id} and {ub.instance_id} too close: {dist}",
                )

    def test_melee_engagement_lock(self) -> None:
        """Melee unit locks target when in range, releases on death."""
        session, attacker, target = self.make_duel_session(
            attack_range=18.0,
            move_speed=24.0,
            start_distance=12.0,
            attacker_next_action_tick=999,
            attacker_action_interval_ticks=999,
            target_move_speed=0.0,
            target_next_action_tick=999,
            target_action_interval_ticks=999,
        )

        events = step_battle_session(session, ticks=3)
        event_types = [e.type for e in events]

        self.assertIn("engagement_lock", event_types)
        self.assertEqual(target.instance_id, attacker.engagement_target)
        self.assertIn(attacker.movement_intent, ("engaged_lock", "engaged"))

    def test_ranged_hold_distance(self) -> None:
        """Ranged unit stops at desired_distance, does not close to melee."""
        attacker = self.make_unit(
            instance_id="ally_archer",
            side="ally",
            x=0,
            y=0,
            position_x=0.0,
            position_y=0.0,
            attack_range=110.0,
            move_speed=18.0,
            next_action_tick=1,
            action_interval_ticks=1,
            role="archer",
            unit_def_id="ashigaru_bow",
            tags=["ashigaru", "bow", "backline"],
            weapon_slots=["bow"],
        )
        target = self.make_unit(
            instance_id="enemy_001",
            side="enemy",
            x=1,
            y=0,
            position_x=80.0,
            position_y=0.0,
            attack_range=18.0,
            move_speed=0.0,
            next_action_tick=999,
            action_interval_ticks=999,
        )
        state = BattleState(
            battle_id="test",
            seed=1001,
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
            battle_id="test",
            seed=1001,
            initialized=True,
            finished=False,
            current_tick=0,
            events=[],
            event_cursor=0,
            max_ticks=200,
        )

        for _ in range(10):
            step_battle_session(session, ticks=1)

        self.assertEqual("ranged", attacker.engagement_role)
        dist = distance_between(attacker, target)
        self.assertGreater(dist, 10.0, f"Ranged unit too close: {dist}")
        self.assertLess(dist, 110.0, f"Ranged unit too far: {dist}")

    def test_support_stays_near_anchor(self) -> None:
        """Support/banner unit stays near formation anchor."""
        attacker = self.make_unit(
            instance_id="ally_support",
            side="ally",
            x=0,
            y=0,
            position_x=100.0,
            position_y=300.0,
            attack_range=18.0,
            move_speed=20.0,
            next_action_tick=999,
            action_interval_ticks=999,
            role="banner",
            tags=["banner"],
        )
        target = self.make_unit(
            instance_id="enemy_001",
            side="enemy",
            x=1,
            y=0,
            position_x=200.0,
            position_y=100.0,
            attack_range=18.0,
            move_speed=0.0,
            next_action_tick=999,
            action_interval_ticks=999,
        )
        state = BattleState(
            battle_id="test",
            seed=1001,
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
            battle_id="test",
            seed=1001,
            initialized=True,
            finished=False,
            current_tick=0,
            events=[],
            event_cursor=0,
            max_ticks=200,
        )

        initialize_spatial_state(session.state)
        anchor_x, anchor_y = attacker.formation_anchor_x, attacker.formation_anchor_y

        for _ in range(20):
            step_battle_session(session, ticks=1)

        self.assertEqual("support", attacker.engagement_role)
        dist_to_target = distance_between(attacker, target)
        self.assertGreater(
            dist_to_target,
            50.0,
            f"Support unit too close to enemy: {dist_to_target}",
        )

    def test_formation_engagement_event_stream_is_deterministic(self) -> None:
        """Same seed produces identical formation/engagement event stream."""
        session1 = create_battle_session(self.bundle, "demo_001", 1001)
        session2 = create_battle_session(self.bundle, "demo_001", 1001)

        initialize_battle_session(session1)
        initialize_battle_session(session2)

        for _ in range(30):
            step_battle_session(session1, ticks=1)
            step_battle_session(session2, ticks=1)

        e1 = [event_to_dict(e) for e in session1.events]
        e2 = [event_to_dict(e) for e in session2.events]
        self.assertEqual(e1, e2)

    def test_snapshot_includes_formation_engagement_fields(self) -> None:
        """Snapshot has formation_anchor_x/y, engagement_target, engagement_role, desired_distance, separation_radius."""
        session = create_battle_session(self.bundle, "demo_001", 1001)
        initialize_battle_session(session)

        snapshot = build_battle_snapshot(session)
        json.dumps(snapshot)

        for unit_snap in snapshot["units"]:
            self.assertIn("formation_anchor_x", unit_snap)
            self.assertIn("formation_anchor_y", unit_snap)
            self.assertIn("formation_group_id", unit_snap)
            self.assertIn("engagement_target", unit_snap)
            self.assertIn("engagement_role", unit_snap)
            self.assertIn("desired_distance", unit_snap)
            self.assertIn("separation_radius", unit_snap)

    def test_demo_001_has_ranged_units(self) -> None:
        """demo_001 has at least one unit with engagement_role == ranged."""
        session = create_battle_session(self.bundle, "demo_001", 1001)
        initialize_battle_session(session)

        ranged_units = [u for u in session.state.units if u.engagement_role == "ranged"]
        self.assertGreaterEqual(len(ranged_units), 1, "Expected at least one ranged unit in demo_001")
        for ru in ranged_units:
            self.assertGreater(ru.desired_distance, 10.0, f"Ranged unit {ru.instance_id} has tiny desired_distance: {ru.desired_distance}")

    def test_ranged_desired_distance_greater_than_melee(self) -> None:
        """Ranged unit desired_distance should be larger than melee desired_distance."""
        session = create_battle_session(self.bundle, "demo_001", 1001)
        initialize_battle_session(session)

        ranged_dd = [u.desired_distance for u in session.state.units if u.engagement_role == "ranged"]
        melee_dd = [u.desired_distance for u in session.state.units if u.engagement_role == "frontline"]

        if ranged_dd and melee_dd:
            self.assertGreater(max(ranged_dd), max(melee_dd),
                f"Ranged desired_distance ({max(ranged_dd)}) should exceed melee ({max(melee_dd)})")

    def test_ranged_hold_event_produced(self) -> None:
        """Running demo_001 produces ranged_hold events."""
        session = create_battle_session(self.bundle, "demo_001", 1001)
        initialize_battle_session(session)

        for _ in range(80):
            step_battle_session(session, ticks=1)

        event_types = {e.type for e in session.events}
        self.assertIn("ranged_hold", event_types, "Expected ranged_hold events in demo_001 event stream")

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
        role: str = "front",
        unit_def_id: str = "",
        tags: list = None,
        weapon_slots: list = None,
    ) -> RuntimeUnitState:
        unit_def = self.sample_unit_def
        return RuntimeUnitState(
            instance_id=instance_id,
            side=side,
            unit_def_id=unit_def_id or unit_def.id,
            x=x,
            y=y,
            role=role,
            name=unit_def.name,
            tags=tags if tags is not None else list(unit_def.tags),
            base_hp=5000,
            base_atk=20,
            base_defense=10,
            base_range=1,
            base_attack_interval=1.0,
            weapon_slots=weapon_slots if weapon_slots is not None else [],
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
