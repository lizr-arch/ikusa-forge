"""Shared spatial utility functions used by spatial_combat and engagement_system."""

import math
from typing import List, Optional

from ikusa_sim.runtime_models import BattleState, UnitState


def distance_between(left: UnitState, right: UnitState) -> float:
    return math.hypot(left.position_x - right.position_x, left.position_y - right.position_y)


def in_attack_range(unit: UnitState, target: UnitState) -> bool:
    return distance_between(unit, target) <= unit.attack_range + 0.001


def nearest_alive_enemy(unit: UnitState, units: List[UnitState]) -> Optional[UnitState]:
    enemies = [candidate for candidate in units if candidate.alive and candidate.side != unit.side]
    if not enemies:
        return None
    enemies.sort(key=lambda candidate: (distance_between(unit, candidate), candidate.instance_id))
    return enemies[0]


def unit_by_id(units: List[UnitState], unit_id: Optional[str]) -> Optional[UnitState]:
    if not unit_id:
        return None
    for u in units:
        if u.instance_id == unit_id:
            return u
    return None


def format_event_id(sequence_number: int) -> str:
    return f"evt_{sequence_number:06d}"


def next_event_id(state: BattleState) -> str:
    event_id = format_event_id(state._next_event_number)
    state._next_event_number += 1
    return event_id


def angle_to(unit: UnitState, target: UnitState) -> float:
    return math.degrees(math.atan2(target.position_y - unit.position_y, target.position_x - unit.position_x))
