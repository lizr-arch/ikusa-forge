"""Formation System / 编队系统 for Ikusa Forge Phase 2.

This module manages formation anchors and group advance behavior.
"""

import math
from typing import List, Optional

from ikusa_sim.events import BattleEvent
from ikusa_sim.runtime_models import BattleState, UnitState
from ikusa_sim.spatial_utils import next_event_id


def initialize_formation_anchors(state: BattleState) -> None:
    """Set initial formation anchors from the encounter grid and side.

    The anchor for each unit is derived from its current position_x/y + the
    side's initial centroid offset. This preserves the relative layout from the
    encounter grid.
    """
    for side in ("ally", "enemy"):
        side_units = [u for u in state.units if u.side == side and u.alive]
        if not side_units:
            continue
        centroid_x, centroid_y = _centroid_of(side_units)
        for unit in side_units:
            if unit.formation_anchor_x == 0.0 and unit.formation_anchor_y == 0.0:
                unit.formation_anchor_x = unit.position_x
                unit.formation_anchor_y = unit.position_y


def update_formation_anchors(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
) -> None:
    """Advance each side's formation toward the enemy side centroid.

    The group center moves toward the enemy centroid at a fraction of move_speed.
    Individual anchors maintain their relative offset from the group center.
    This is a simple linear group push, not A* pathfinding.
    """
    ally_units = [u for u in state.units if u.side == "ally" and u.alive]
    enemy_units = [u for u in state.units if u.side == "enemy" and u.alive]

    if not ally_units or not enemy_units:
        return

    ally_centroid_x, ally_centroid_y = _centroid_of(ally_units)
    enemy_centroid_x, enemy_centroid_y = _centroid_of(enemy_units)

    step_size = _group_step_size(state)
    _advance_side(ally_units, enemy_centroid_x, enemy_centroid_y, step_size,
                  state, events, tick, reason="group_advance")
    _advance_side(enemy_units, ally_centroid_x, ally_centroid_y, step_size,
                  state, events, tick, reason="group_advance")


def formation_anchor_for_unit(
    unit: UnitState,
    state: BattleState,
) -> tuple:
    """Return (anchor_x, anchor_y) for a given unit."""
    return (unit.formation_anchor_x, unit.formation_anchor_y)


def formation_cohesion_score(unit: UnitState) -> float:
    """Measure how far the unit is from its formation anchor."""
    dx = unit.position_x - unit.formation_anchor_x
    dy = unit.position_y - unit.formation_anchor_y
    return math.hypot(dx, dy)


def side_centroid(state: BattleState, side: str) -> tuple:
    """Compute the average position of alive units on a given side."""
    alive = [u for u in state.units if u.side == side and u.alive]
    if not alive:
        return (0.0, 0.0)
    return _centroid_of(alive)


def _centroid_of(units: list) -> tuple:
    n = len(units)
    if n == 0:
        return (0.0, 0.0)
    sum_x = sum(u.position_x for u in units)
    sum_y = sum(u.position_y for u in units)
    return (sum_x / n, sum_y / n)


def _group_step_size(state: BattleState) -> float:
    """How far the group center advances per tick.

    Uses the average move_speed of all alive units divided by tick_rate.
    """
    alive = [u for u in state.units if u.alive]
    if not alive:
        return 0.0
    avg_speed = sum(u.move_speed for u in alive) / len(alive)
    return avg_speed / float(max(1, state.tick_rate))


def _advance_side(
    side_units: list,
    target_x: float,
    target_y: float,
    step_size: float,
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    reason: str,
) -> None:
    """Move all anchors for a side toward a target position."""
    if not side_units:
        return

    old_centroid_x, old_centroid_y = _centroid_of(side_units)
    dx = target_x - old_centroid_x
    dy = target_y - old_centroid_y
    dist = math.hypot(dx, dy)
    if dist < 0.5:
        return

    actual_step = min(step_size, dist)
    dir_x = dx / dist * actual_step
    dir_y = dy / dist * actual_step

    new_centroid_x = old_centroid_x + dir_x
    new_centroid_y = old_centroid_y + dir_y

    for unit in sorted(side_units, key=lambda u: u.instance_id):
        offset_x = unit.formation_anchor_x - old_centroid_x
        offset_y = unit.formation_anchor_y - old_centroid_y
        new_anchor_x = new_centroid_x + offset_x
        new_anchor_y = new_centroid_y + offset_y

        dx_anchor = new_anchor_x - unit.formation_anchor_x
        dy_anchor = new_anchor_y - unit.formation_anchor_y
        anchor_delta = math.hypot(dx_anchor, dy_anchor)

        unit.formation_anchor_x = new_anchor_x
        unit.formation_anchor_y = new_anchor_y

        if tick % 10 == 0 or anchor_delta > 20.0:
            events.append(
                BattleEvent(
                    tick=tick,
                    event_id=next_event_id(state),
                    type="formation_anchor_update",
                    payload={
                        "unit": unit.instance_id,
                        "anchor_x": round(new_anchor_x, 3),
                        "anchor_y": round(new_anchor_y, 3),
                        "group_id": unit.formation_group_id,
                        "reason": reason,
                    },
                )
            )
