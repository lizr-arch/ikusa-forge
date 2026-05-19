"""Spatial combat helpers for Ikusa Forge realtime combat.

This module keeps the continuous-position and engagement logic separate from
the session orchestration layer so the runtime can reuse the same spatial
rules from battles, tests, and any future viewers.

Phase 2: integrated with Formation System / 编队系统 and
Engagement System / 接敌系统 for role-based movement, anchoring,
and separation.
"""

import math
from typing import List, Optional

from ikusa_sim.decisions import MovementDecision
from ikusa_sim.engagement_system import update_engagement_pairs
from ikusa_sim.events import BattleEvent
from ikusa_sim.formation_system import initialize_formation_anchors, update_formation_anchors
from ikusa_sim.runtime_models import BattleState, UnitState
from ikusa_sim.spatial_utils import (
    angle_to,
    distance_between,
    in_attack_range,
    nearest_alive_enemy,
    next_event_id,
    unit_by_id,
)
from ikusa_sim.targeting import TargetCandidateScore, TargetDecision, select_target_decision
from ikusa_sim.unit_fsm import UnitCombatState, get_unit_combat_state, set_unit_combat_state

_SEPARATION_PUSH = 1.5
_EVENT_THROTTLE = 5


def initialize_spatial_state(state: BattleState) -> None:
    initialize_formation_anchors(state)
    for unit in state.units:
        unit.velocity_x = 0.0
        unit.velocity_y = 0.0
        if not unit.alive:
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
    update_formation_anchors(state, events, tick)
    update_engagement_pairs(state, events, tick)

    alive_units = sorted(
        (u for u in state.units if u.alive),
        key=lambda u: u.instance_id,
    )

    for unit in alive_units:
        intent = unit.movement_intent

        if intent in ("engaged", "engaged_lock"):
            _handle_engaged_unit(state, events, tick, unit)

        elif intent == "hold_range":
            _handle_ranged_holding(state, events, tick, unit)

        elif intent == "hold":
            _handle_holding_unit(state, events, tick, unit)

        elif intent == "move_to_engage":
            _handle_moving_unit(state, events, tick, unit)

        elif intent == "retreat_range":
            _handle_retreating_unit(state, events, tick, unit)

        elif intent == "move_to_anchor":
            _handle_move_to_anchor(state, events, tick, unit)

        else:
            _handle_moving_unit(state, events, tick, unit)

    _apply_separation(state, alive_units)


def move_toward_target(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
    target: UnitState,
) -> None:
    _move_unit_toward(state, events, tick, unit, target, unit.attack_range, "move_to_attack_range")


def select_engaged_target_decision(attacker: UnitState, units: List[UnitState]) -> TargetDecision:
    target_id = attacker.engaged_target or attacker.engagement_target
    target = unit_by_id(units, target_id)
    if target is not None and target.alive and target.side != attacker.side and in_attack_range(attacker, target):
        dist = distance_between(attacker, target)
        score = TargetCandidateScore(
            unit_id=target.instance_id,
            final_score=max(0, int(1000.0 - dist)),
            exposure_score=max(0, int(200.0 - dist)),
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
    target_id = unit.engaged_target or unit.engagement_target
    target = unit_by_id(units, target_id)
    return target is not None and target.alive and target.side != unit.side and in_attack_range(unit, target)


def _handle_engaged_unit(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
) -> None:
    target_id = unit.engaged_target or unit.engagement_target
    target = unit_by_id(state.units, target_id)
    if target is None or not target.alive:
        return

    previous_intent = unit.movement_intent
    unit.velocity_x = 0.0
    unit.velocity_y = 0.0
    unit.facing_angle = angle_to(unit, target)

    if not _has_entered_range_for(unit, target_id):
        _mark_entered_range(unit, target_id)
        _emit_enter_range_events(state, events, tick, unit, target, distance_between(unit, target))

    set_unit_combat_state(unit, UnitCombatState.ENGAGED, reason="attack_range_reached")
    if previous_intent == "move_to_engage":
        unit.movement_intent = "engaged_lock" if unit.engagement_role in ("frontline", "flanker") else "engaged"


def _handle_ranged_holding(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
) -> None:
    target_id = unit.engaged_target or unit.engagement_target
    target = unit_by_id(state.units, target_id)
    if target is None or not target.alive:
        return

    unit.velocity_x = 0.0
    unit.velocity_y = 0.0
    unit.facing_angle = angle_to(unit, target)
    set_unit_combat_state(unit, UnitCombatState.ENGAGED, reason="ranged_hold")

    if not _has_entered_range_for(unit, target_id):
        _mark_entered_range(unit, target_id)
        _emit_enter_range_events(state, events, tick, unit, target, distance_between(unit, target))


def _handle_holding_unit(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
) -> None:
    target_id = unit.engaged_target or unit.engagement_target
    target = unit_by_id(state.units, target_id)
    if target is not None and target.alive and in_attack_range(unit, target):
        unit.velocity_x = 0.0
        unit.velocity_y = 0.0
        unit.facing_angle = angle_to(unit, target)
        if not _has_entered_range_for(unit, target_id):
            _mark_entered_range(unit, target_id)
            _emit_enter_range_events(state, events, tick, unit, target, distance_between(unit, target))
        return

    unit.velocity_x = 0.0
    unit.velocity_y = 0.0
    set_unit_combat_state(unit, UnitCombatState.IDLE, reason="holding")


def _handle_moving_unit(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
) -> None:
    target_id = unit.engagement_target or unit.engaged_target
    target = unit_by_id(state.units, target_id)

    if target is not None and target.alive:
        dist = distance_between(unit, target)

        if _should_emit_target_acquired(unit, target):
            events.append(
                BattleEvent(
                    tick=tick,
                    event_id=next_event_id(state),
                    type="target_acquired",
                    payload={
                        "unit": unit.instance_id,
                        "target": target.instance_id,
                        "distance": round(dist, 3),
                        "reason": "nearest_enemy",
                    },
                )
            )
            unit.engaged_target = target.instance_id
            unit._acquired_target_id = target.instance_id
        if in_attack_range(unit, target):
            unit.velocity_x = 0.0
            unit.velocity_y = 0.0
            unit.facing_angle = angle_to(unit, target)
            if not _has_entered_range_for(unit, target_id):
                _mark_entered_range(unit, target_id)
                _emit_enter_range_events(state, events, tick, unit, target, dist)
                unit.movement_intent = "engaged_lock" if unit.engagement_role in ("frontline", "flanker") else "engaged"
            return

        stop_distance = unit.desired_distance if unit.engagement_role == "ranged" else unit.attack_range
        if unit.engagement_role == "ranged" and dist <= stop_distance + 0.001:
            unit.velocity_x = 0.0
            unit.velocity_y = 0.0
            unit.facing_angle = angle_to(unit, target)
            unit.movement_intent = "hold_range"
            return

        _move_unit_toward(state, events, tick, unit, target, stop_distance, "move_to_attack_range")
        return

    anchor_x, anchor_y = unit.formation_anchor_x, unit.formation_anchor_y
    dx = anchor_x - unit.position_x
    dy = anchor_y - unit.position_y
    anchor_dist = math.hypot(dx, dy)
    if anchor_dist < 1.0:
        unit.velocity_x = 0.0
        unit.velocity_y = 0.0
        unit.movement_intent = "hold"
        return

    step_distance = unit.move_speed / float(max(1, state.tick_rate))
    actual_step = min(step_distance, anchor_dist)
    dir_x = dx / anchor_dist
    dir_y = dy / anchor_dist

    old_x = unit.position_x
    old_y = unit.position_y
    unit.position_x += dir_x * actual_step
    unit.position_y += dir_y * actual_step
    unit.velocity_x = dir_x * unit.move_speed if actual_step > 0 else 0.0
    unit.velocity_y = dir_y * unit.move_speed if actual_step > 0 else 0.0
    unit.facing_angle = math.degrees(math.atan2(dir_y, dir_x))
    unit.movement_intent = "move_to_engage"
    set_unit_combat_state(unit, UnitCombatState.MOVING_TO_ENGAGE, reason="move_to_anchor")

    if actual_step > 0 and tick % _EVENT_THROTTLE == 0:
        events.append(
            BattleEvent(
                tick=tick,
                event_id=next_event_id(state),
                type="unit_move",
                payload={
                    "unit": unit.instance_id,
                    "target": None,
                    "from_x": round(old_x, 3),
                    "from_y": round(old_y, 3),
                    "to_x": round(unit.position_x, 3),
                    "to_y": round(unit.position_y, 3),
                    "velocity_x": round(unit.velocity_x, 3),
                    "velocity_y": round(unit.velocity_y, 3),
                    "move_speed": unit.move_speed,
                    "distance_to_target": round(math.hypot(unit.position_x - anchor_x, unit.position_y - anchor_y), 3),
                    "reason": "move_to_anchor",
                },
            )
        )


def _handle_move_to_anchor(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
) -> None:
    anchor_x, anchor_y = unit.formation_anchor_x, unit.formation_anchor_y
    dx = anchor_x - unit.position_x
    dy = anchor_y - unit.position_y
    anchor_dist = math.hypot(dx, dy)
    if anchor_dist < 1.0:
        unit.velocity_x = 0.0
        unit.velocity_y = 0.0
        unit.movement_intent = "hold"
        return

    step_distance = unit.move_speed / float(max(1, state.tick_rate))
    actual_step = min(step_distance, anchor_dist)
    dir_x = dx / anchor_dist
    dir_y = dy / anchor_dist

    old_x = unit.position_x
    old_y = unit.position_y
    unit.position_x += dir_x * actual_step
    unit.position_y += dir_y * actual_step
    unit.velocity_x = dir_x * unit.move_speed if actual_step > 0 else 0.0
    unit.velocity_y = dir_y * unit.move_speed if actual_step > 0 else 0.0
    unit.facing_angle = math.degrees(math.atan2(dir_y, dir_x))
    unit.movement_intent = "move_to_anchor"
    set_unit_combat_state(unit, UnitCombatState.MOVING_TO_FORMATION, reason="follow_anchor")

    if actual_step > 0 and tick % _EVENT_THROTTLE == 0:
        events.append(
            BattleEvent(
                tick=tick,
                event_id=next_event_id(state),
                type="unit_move",
                payload={
                    "unit": unit.instance_id,
                    "target": None,
                    "from_x": round(old_x, 3),
                    "from_y": round(old_y, 3),
                    "to_x": round(unit.position_x, 3),
                    "to_y": round(unit.position_y, 3),
                    "velocity_x": round(unit.velocity_x, 3),
                    "velocity_y": round(unit.velocity_y, 3),
                    "move_speed": unit.move_speed,
                    "distance_to_target": round(math.hypot(unit.position_x - anchor_x, unit.position_y - anchor_y), 3),
                    "reason": "move_to_anchor",
                },
            )
        )


def _handle_retreating_unit(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
) -> None:
    target_id = unit.engaged_target or unit.engagement_target
    target = unit_by_id(state.units, target_id)
    if target is None or not target.alive:
        unit.movement_intent = "hold"
        return

    dx = unit.position_x - target.position_x
    dy = unit.position_y - target.position_y
    dist = math.hypot(dx, dy)
    if dist < 0.001:
        dx = 1.0
        dy = 0.0
        dist = 1.0
    dir_x = dx / dist
    dir_y = dy / dist

    step_distance = unit.move_speed / float(max(1, state.tick_rate)) * 0.5
    old_x = unit.position_x
    old_y = unit.position_y
    unit.position_x += dir_x * step_distance
    unit.position_y += dir_y * step_distance
    unit.velocity_x = dir_x * unit.move_speed * 0.5
    unit.velocity_y = dir_y * unit.move_speed * 0.5
    unit.facing_angle = math.degrees(math.atan2(dy, dx))
    set_unit_combat_state(unit, UnitCombatState.MOVING_TO_ENGAGE, reason="retreat_range")

    if tick % _EVENT_THROTTLE == 0:
        events.append(
            BattleEvent(
                tick=tick,
                event_id=next_event_id(state),
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
                    "distance_to_target": round(distance_between(unit, target), 3),
                    "reason": "retreat_range",
                },
            )
        )


def _move_unit_toward(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
    target: UnitState,
    stop_distance: float,
    reason: str,
) -> None:
    dist = distance_between(unit, target)
    if dist <= 0:
        unit.velocity_x = 0.0
        unit.velocity_y = 0.0
        unit.movement_intent = "engaged"
        set_unit_combat_state(unit, UnitCombatState.ENGAGED, reason="zero_distance_engage")
        return

    step_distance = unit.move_speed / float(max(1, state.tick_rate))
    desired_step = max(0.0, dist - stop_distance)
    actual_step = min(step_distance, desired_step)

    MovementDecision(
        unit_id=unit.instance_id,
        intent="move_to_attack_range",
        target_id=target.instance_id,
        destination_x=target.position_x,
        destination_y=target.position_y,
        reason=reason,
        score=max(0.0, dist - stop_distance),
    )
    direction_x = (target.position_x - unit.position_x) / dist
    direction_y = (target.position_y - unit.position_y) / dist

    old_x = unit.position_x
    old_y = unit.position_y
    unit.position_x += direction_x * actual_step
    unit.position_y += direction_y * actual_step
    unit.velocity_x = direction_x * unit.move_speed if actual_step > 0 else 0.0
    unit.velocity_y = direction_y * unit.move_speed if actual_step > 0 else 0.0
    unit.facing_angle = math.degrees(math.atan2(direction_y, direction_x))
    unit.movement_intent = "move_to_attack_range"
    set_unit_combat_state(unit, UnitCombatState.MOVING_TO_ENGAGE, reason=reason)

    distance_after = distance_between(unit, target)
    if actual_step > 0 and (tick % _EVENT_THROTTLE == 0 or distance_after <= stop_distance + 0.001):
        events.append(
            BattleEvent(
                tick=tick,
                event_id=next_event_id(state),
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
                    "reason": reason,
                },
            )
        )


def _apply_separation(state: BattleState, units: List[UnitState]) -> None:
    for i, unit_a in enumerate(units):
        for unit_b in units[i + 1:]:
            if unit_a.side != unit_b.side:
                continue
            dist = distance_between(unit_a, unit_b)
            min_dist = max(unit_a.separation_radius, unit_b.separation_radius)
            if dist >= min_dist:
                continue
            if dist < 0.001:
                dist = 0.001
                dx = _stable_xor_float(unit_a.instance_id, unit_b.instance_id, 1.0)
                dy = _stable_xor_float(unit_b.instance_id, unit_a.instance_id, 1.0)
            else:
                dx = (unit_a.position_x - unit_b.position_x) / dist
                dy = (unit_a.position_y - unit_b.position_y) / dist

            push = (min_dist - dist) * 0.5 / float(max(1, state.tick_rate))
            push = min(push, _SEPARATION_PUSH)
            unit_a.position_x += dx * push
            unit_a.position_y += dy * push
            unit_b.position_x -= dx * push
            unit_b.position_y -= dy * push


def _has_entered_range_for(unit: UnitState, target_id: str) -> bool:
    return getattr(unit, "_entered_range_targets", None) is not None and target_id in unit._entered_range_targets


def _mark_entered_range(unit: UnitState, target_id: str) -> None:
    if not hasattr(unit, "_entered_range_targets") or unit._entered_range_targets is None:
        unit._entered_range_targets = set()
    unit._entered_range_targets.add(target_id)


def _should_emit_target_acquired(unit: UnitState, target: UnitState) -> bool:
    acquired = getattr(unit, "_acquired_target_id", None)
    return acquired != target.instance_id


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
            event_id=next_event_id(state),
            type="enter_range",
            payload=payload,
        )
    )
    events.append(
        BattleEvent(
            tick=tick,
            event_id=next_event_id(state),
            type="engage_start",
            payload={**payload, "reason": "attack_range_reached"},
        )
    )


def _stable_xor_float(a: str, b: str, fallback: float) -> float:
    return fallback if a < b else -fallback
