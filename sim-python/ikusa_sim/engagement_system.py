"""Engagement System / 接敌系统 for Ikusa Forge Phase 2.

This module manages engagement pairing, melee lock, ranged hold distance,
and role-based targeting behavior.
"""

import math
from typing import List, Optional

from ikusa_sim.events import BattleEvent
from ikusa_sim.runtime_models import BattleState, UnitState
from ikusa_sim.spatial_utils import distance_between, in_attack_range, nearest_alive_enemy, next_event_id, unit_by_id


def update_engagement_pairs(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
) -> None:
    for unit in sorted(
        (u for u in state.units if u.alive),
        key=lambda u: u.instance_id,
    ):
        _update_unit_engagement(unit, state, events, tick)


def choose_engagement_target(
    unit: UnitState,
    enemies: List[UnitState],
) -> Optional[UnitState]:
    if not enemies:
        return None
    return nearest_alive_enemy(unit, enemies)


def lock_melee_engagement(
    unit: UnitState,
    target: UnitState,
    events: List[BattleEvent],
    tick: int,
    state: BattleState,
) -> None:
    unit.engagement_target = target.instance_id
    unit.movement_intent = "engaged_lock"
    unit._lock_emitted = True

    distance = round(distance_between(unit, target), 3)
    events.append(
        BattleEvent(
            tick=tick,
            event_id=next_event_id(state),
            type="engagement_lock",
            payload={
                "unit": unit.instance_id,
                "target": target.instance_id,
                "role": unit.engagement_role,
                "distance": distance,
                "reason": "melee_entered_range",
            },
        )
    )


def release_engagement(
    unit: UnitState,
    target_id: str,
    events: List[BattleEvent],
    tick: int,
    state: BattleState,
    reason: str = "target_dead",
) -> None:
    if unit.engagement_target == target_id:
        unit.engagement_target = None
        unit.engaged_target = None
        unit.movement_intent = "hold"
        unit._lock_emitted = False
        events.append(
            BattleEvent(
                tick=tick,
                event_id=next_event_id(state),
                type="engagement_release",
                payload={
                    "unit": unit.instance_id,
                    "target": target_id,
                    "reason": reason,
                },
            )
        )


def should_hold_ranged_distance(
    unit: UnitState,
    target: UnitState,
) -> bool:
    role = unit.engagement_role
    if role != "ranged":
        return False
    distance = distance_between(unit, target)
    return distance <= unit.desired_distance + 1.0


def desired_engagement_distance(
    unit: UnitState,
    target: UnitState,
) -> float:
    return unit.desired_distance


def _update_unit_engagement(
    unit: UnitState,
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
) -> None:
    enemies = [u for u in state.units if u.alive and u.side != unit.side]

    if not enemies:
        if unit.engagement_target:
            release_engagement(unit, unit.engagement_target, events, tick, state, "no_enemies")
        return

    current_target = unit_by_id(state.units, unit.engagement_target)
    if current_target and not current_target.alive:
        release_engagement(unit, unit.engagement_target, events, tick, state, "target_dead")
        current_target = None

    role = unit.engagement_role

    if role in ("frontline", "flanker"):
        _handle_melee_engagement(unit, enemies, state, events, tick)
    elif role == "ranged":
        _handle_ranged_engagement(unit, enemies, state, events, tick)
    elif role == "support":
        _handle_support_engagement(unit, enemies, state, events, tick)


def _handle_melee_engagement(
    unit: UnitState,
    enemies: List[UnitState],
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
) -> None:
    current_target = unit_by_id(state.units, unit.engagement_target)
    if current_target and current_target.alive:
        if in_attack_range(unit, current_target):
            if not getattr(unit, "_lock_emitted", False):
                lock_melee_engagement(unit, current_target, events, tick, state)
            else:
                unit.movement_intent = "engaged_lock"
                unit.engaged_target = current_target.instance_id
            return
        unit.movement_intent = "move_to_engage"
        return

    target = choose_engagement_target(unit, enemies)
    if target is None:
        return

    if in_attack_range(unit, target):
        lock_melee_engagement(unit, target, events, tick, state)
    else:
        unit.engagement_target = target.instance_id
        unit.movement_intent = "move_to_engage"


def _handle_ranged_engagement(
    unit: UnitState,
    enemies: List[UnitState],
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
) -> None:
    target = choose_engagement_target(unit, enemies)
    if target is None:
        return

    unit.engagement_target = target.instance_id

    distance = distance_between(unit, target)
    if should_hold_ranged_distance(unit, target):
        unit.movement_intent = "hold_range"
        events.append(
            BattleEvent(
                tick=tick,
                event_id=next_event_id(state),
                type="ranged_hold",
                payload={
                    "unit": unit.instance_id,
                    "target": target.instance_id,
                    "distance": round(distance, 3),
                    "desired_distance": unit.desired_distance,
                    "reason": "hold_attack_range",
                },
            )
        )
    elif distance > unit.desired_distance:
        unit.movement_intent = "move_to_engage"
    else:
        unit.movement_intent = "retreat_range"


def _handle_support_engagement(
    unit: UnitState,
    enemies: List[UnitState],
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
) -> None:
    target = choose_engagement_target(unit, enemies)
    if target is None:
        return

    unit.engagement_target = target.instance_id

    distance = distance_between(unit, target)
    if distance <= unit.engagement_range:
        unit.movement_intent = "move_to_engage"
    else:
        unit.movement_intent = "move_to_anchor"
