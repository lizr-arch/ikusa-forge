"""Spatial combat helpers for Ikusa Forge realtime combat.

This module keeps the continuous-position and engagement logic separate from
the session orchestration layer so the runtime can reuse the same spatial
rules from battles, tests, and any future viewers.
"""

import math
from typing import List, Optional

from ikusa_sim.decisions import MovementDecision
from ikusa_sim.events import BattleEvent
from ikusa_sim.runtime_models import BattleState, UnitState
from ikusa_sim.targeting import TargetCandidateScore, TargetDecision, select_target_decision
from ikusa_sim.unit_fsm import UnitCombatState, get_unit_combat_state, set_unit_combat_state


def initialize_spatial_state(state: BattleState) -> None:
    for unit in state.units:
        unit.velocity_x = 0.0
        unit.velocity_y = 0.0
        if not unit.alive:
            # dead units should not keep stale spatial intent
            set_unit_combat_state(unit, UnitCombatState.DEAD, reason="initialize_spatial_state")
            unit.movement_intent = "hold"
            unit.engaged_target = None
            continue
        if get_unit_combat_state(unit) == UnitCombatState.DEAD.value:
            set_unit_combat_state(unit, UnitCombatState.IDLE, reason="initialize_spatial_state")
        if not unit.movement_intent:
            unit.movement_intent = "hold"


def update_spatial_engagements(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
) -> None:
    for unit in sorted((candidate for candidate in state.units if candidate.alive), key=lambda item: item.instance_id):
        target = nearest_alive_enemy(unit, state.units)
        if target is None:
            unit.engaged_target = None
            unit.velocity_x = 0.0
            unit.velocity_y = 0.0
            unit.movement_intent = "hold"
            set_unit_combat_state(unit, UnitCombatState.IDLE, reason="no_enemy_target")
            continue

        previous_target = unit.engaged_target
        previous_intent = unit.movement_intent
        distance_before = distance_between(unit, target)
        if previous_target != target.instance_id:
            unit.engaged_target = target.instance_id
            events.append(
                BattleEvent(
                    tick=tick,
                    event_id=_next_event_id(state),
                    type="target_acquired",
                    payload={
                        "unit": unit.instance_id,
                        "target": target.instance_id,
                        "distance": round(distance_before, 3),
                        "reason": "nearest_enemy",
                    },
                )
            )

        if in_attack_range(unit, target):
            unit.velocity_x = 0.0
            unit.velocity_y = 0.0
            unit.facing_angle = _angle_to(unit, target)
            unit.movement_intent = "engaged"
            set_unit_combat_state(unit, UnitCombatState.ENGAGED, reason="attack_range_reached")
            if previous_intent != "engaged" or previous_target != target.instance_id:
                _emit_enter_range_events(state, events, tick, unit, target, distance_before)
            continue

        move_toward_target(state, events, tick, unit, target)

        distance_after = distance_between(unit, target)
        if in_attack_range(unit, target) and (previous_intent != "engaged" or previous_target != target.instance_id):
            unit.movement_intent = "engaged"
            unit.velocity_x = 0.0
            unit.velocity_y = 0.0
            set_unit_combat_state(unit, UnitCombatState.ENGAGED, reason="attack_range_reached")
            _emit_enter_range_events(state, events, tick, unit, target, distance_after)


def move_toward_target(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
    target: UnitState,
) -> None:
    distance = distance_between(unit, target)
    if distance <= 0:
        unit.velocity_x = 0.0
        unit.velocity_y = 0.0
        unit.movement_intent = "engaged"
        set_unit_combat_state(unit, UnitCombatState.ENGAGED, reason="zero_distance_engage")
        return

    step_distance = unit.move_speed / float(max(1, state.tick_rate))
    desired_step = max(0.0, distance - unit.attack_range)
    actual_step = min(step_distance, desired_step)
    movement_decision = MovementDecision(
        unit_id=unit.instance_id,
        intent="move_to_attack_range",
        target_id=target.instance_id,
        destination_x=target.position_x,
        destination_y=target.position_y,
        reason="move_to_attack_range",
        score=max(0.0, distance - unit.attack_range),
    )
    direction_x = (target.position_x - unit.position_x) / distance
    direction_y = (target.position_y - unit.position_y) / distance

    old_x = unit.position_x
    old_y = unit.position_y
    unit.position_x += direction_x * actual_step
    unit.position_y += direction_y * actual_step
    unit.velocity_x = direction_x * unit.move_speed if actual_step > 0 else 0.0
    unit.velocity_y = direction_y * unit.move_speed if actual_step > 0 else 0.0
    unit.facing_angle = math.degrees(math.atan2(direction_y, direction_x))
    unit.movement_intent = movement_decision.intent
    set_unit_combat_state(unit, UnitCombatState.MOVING_TO_ENGAGE, reason=movement_decision.reason)

    distance_after = distance_between(unit, target)
    if actual_step > 0 and (tick % 5 == 0 or distance_after <= unit.attack_range + 0.001):
        events.append(
            BattleEvent(
                tick=tick,
                event_id=_next_event_id(state),
                type="unit_move",
                payload={
                    "unit": unit.instance_id,
                    "target": target.instance_id,
                    "from_x": round(old_x, 3),
                    "from_y": round(old_y, 3),
                    "to_x": round(unit.position_x, 3),
                    "to_y": round(unit.position_y, 3),
                    "velocity_x": round(unit.velocity_x, 3),
                    "velocity_y": round(unit.velocity_y, 3),
                    "move_speed": unit.move_speed,
                    "distance_to_target": round(distance_after, 3),
                    "reason": "move_to_attack_range",
                },
            )
        )


def select_engaged_target_decision(attacker: UnitState, units: List[UnitState]) -> TargetDecision:
    target = _unit_by_id(units, attacker.engaged_target)
    if target is not None and target.alive and target.side != attacker.side and in_attack_range(attacker, target):
        distance = distance_between(attacker, target)
        score = TargetCandidateScore(
            unit_id=target.instance_id,
            final_score=max(0, int(1000.0 - distance)),
            exposure_score=max(0, int(200.0 - distance)),
            column_score=max(0, 40 - abs(attacker.x - target.x) * 10),
            low_hp_score=int((1.0 - (float(target.hp) / float(max(1, target.base_hp)))) * 120),
            threat_score=target.atk + target.range * 4 + (15 if target.skill_ids else 0),
            role_score=0,
            tie_break=0,
        )
        return TargetDecision(
            target=target,
            reason="spatial_engaged_target",
            score=score,
            candidates=[score],
        )
    return select_target_decision(attacker, units)


def engaged_target_in_attack_range(unit: UnitState, units: List[UnitState]) -> bool:
    target = _unit_by_id(units, unit.engaged_target)
    return target is not None and target.alive and target.side != unit.side and in_attack_range(unit, target)


def nearest_alive_enemy(unit: UnitState, units: List[UnitState]) -> Optional[UnitState]:
    enemies = [candidate for candidate in units if candidate.alive and candidate.side != unit.side]
    if not enemies:
        return None
    enemies.sort(key=lambda candidate: (distance_between(unit, candidate), candidate.instance_id))
    return enemies[0]


def distance_between(left: UnitState, right: UnitState) -> float:
    return math.hypot(left.position_x - right.position_x, left.position_y - right.position_y)


def in_attack_range(unit: UnitState, target: UnitState) -> bool:
    return distance_between(unit, target) <= unit.attack_range + 0.001


def _emit_enter_range_events(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
    target: UnitState,
    distance: float,
) -> None:
    payload = {
        "unit": unit.instance_id,
        "target": target.instance_id,
        "distance": round(distance, 3),
        "attack_range": unit.attack_range,
        "engagement_range": unit.engagement_range,
    }
    events.append(
        BattleEvent(
            tick=tick,
            event_id=_next_event_id(state),
            type="enter_range",
            payload=payload,
        )
    )
    events.append(
        BattleEvent(
            tick=tick,
            event_id=_next_event_id(state),
            type="engage_start",
            payload={**payload, "reason": "attack_range_reached"},
        )
    )


def _unit_by_id(units: List[UnitState], unit_id: Optional[str]) -> Optional[UnitState]:
    if not unit_id:
        return None
    for unit in units:
        if unit.instance_id == unit_id:
            return unit
    return None


def _angle_to(unit: UnitState, target: UnitState) -> float:
    return math.degrees(math.atan2(target.position_y - unit.position_y, target.position_x - unit.position_x))


def _format_event_id(sequence_number: int) -> str:
    return f"evt_{sequence_number:06d}"


def _next_event_id(state: BattleState) -> str:
    event_id = _format_event_id(state._next_event_number)
    state._next_event_number += 1
    return event_id
