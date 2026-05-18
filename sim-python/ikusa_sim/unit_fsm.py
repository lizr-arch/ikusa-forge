"""Unit combat state helpers for Ikusa Forge.

This module keeps the unit-level finite state machine lightweight and explicit.
The runtime currently uses it for state bookkeeping rather than for full combat
behavior ownership.
"""

from enum import Enum
from typing import Any


class UnitCombatState(str, Enum):
    IDLE = "idle"
    MOVING_TO_FORMATION = "moving_to_formation"
    MOVING_TO_ENGAGE = "moving_to_engage"
    ENGAGED = "engaged"
    ATTACKING = "attacking"
    CASTING = "casting"
    RECOVERING = "recovering"
    DEAD = "dead"


_TRANSITIONS = {
    UnitCombatState.IDLE.value: {
        UnitCombatState.MOVING_TO_FORMATION.value,
        UnitCombatState.MOVING_TO_ENGAGE.value,
        UnitCombatState.ENGAGED.value,
        UnitCombatState.ATTACKING.value,
        UnitCombatState.CASTING.value,
        UnitCombatState.RECOVERING.value,
        UnitCombatState.DEAD.value,
    },
    UnitCombatState.MOVING_TO_FORMATION.value: {
        UnitCombatState.IDLE.value,
        UnitCombatState.MOVING_TO_ENGAGE.value,
        UnitCombatState.ENGAGED.value,
        UnitCombatState.DEAD.value,
    },
    UnitCombatState.MOVING_TO_ENGAGE.value: {
        UnitCombatState.MOVING_TO_ENGAGE.value,
        UnitCombatState.ENGAGED.value,
        UnitCombatState.ATTACKING.value,
        UnitCombatState.CASTING.value,
        UnitCombatState.RECOVERING.value,
        UnitCombatState.DEAD.value,
    },
    UnitCombatState.ENGAGED.value: {
        UnitCombatState.IDLE.value,
        UnitCombatState.MOVING_TO_ENGAGE.value,
        UnitCombatState.ATTACKING.value,
        UnitCombatState.CASTING.value,
        UnitCombatState.RECOVERING.value,
        UnitCombatState.DEAD.value,
    },
    UnitCombatState.ATTACKING.value: {
        UnitCombatState.ENGAGED.value,
        UnitCombatState.RECOVERING.value,
        UnitCombatState.DEAD.value,
    },
    UnitCombatState.CASTING.value: {
        UnitCombatState.ENGAGED.value,
        UnitCombatState.RECOVERING.value,
        UnitCombatState.DEAD.value,
    },
    UnitCombatState.RECOVERING.value: {
        UnitCombatState.IDLE.value,
        UnitCombatState.MOVING_TO_FORMATION.value,
        UnitCombatState.MOVING_TO_ENGAGE.value,
        UnitCombatState.ENGAGED.value,
        UnitCombatState.DEAD.value,
    },
    UnitCombatState.DEAD.value: {UnitCombatState.DEAD.value},
}


def get_unit_combat_state(unit: Any) -> str:
    if not getattr(unit, "alive", True):
        return UnitCombatState.DEAD.value
    state = _normalize_state(getattr(unit, "combat_state", UnitCombatState.IDLE.value))
    if state == UnitCombatState.DEAD.value:
        return UnitCombatState.DEAD.value
    return state


def set_unit_combat_state(unit: Any, state: Any, reason: str = "") -> str:
    _ = reason
    next_state = _normalize_state(state)
    current_state = get_unit_combat_state(unit)
    if current_state == UnitCombatState.DEAD.value:
        unit.combat_state = UnitCombatState.DEAD.value
        unit.alive = False
        if hasattr(unit, "engaged_target"):
            unit.engaged_target = None
        if hasattr(unit, "movement_intent"):
            unit.movement_intent = "hold"
        if hasattr(unit, "velocity_x"):
            unit.velocity_x = 0.0
        if hasattr(unit, "velocity_y"):
            unit.velocity_y = 0.0
        return UnitCombatState.DEAD.value

    if next_state == UnitCombatState.DEAD.value:
        unit.combat_state = UnitCombatState.DEAD.value
        unit.alive = False
        if hasattr(unit, "engaged_target"):
            unit.engaged_target = None
        if hasattr(unit, "movement_intent"):
            unit.movement_intent = "hold"
        if hasattr(unit, "velocity_x"):
            unit.velocity_x = 0.0
        if hasattr(unit, "velocity_y"):
            unit.velocity_y = 0.0
        return UnitCombatState.DEAD.value

    if not can_transition_unit_state(current_state, next_state):
        return current_state

    unit.combat_state = next_state
    return next_state


def can_transition_unit_state(from_state: Any, to_state: Any) -> bool:
    current = _normalize_state(from_state)
    target = _normalize_state(to_state)
    if current == target:
        return True
    allowed = _TRANSITIONS.get(current)
    return allowed is not None and target in allowed


def _normalize_state(value: Any) -> str:
    if isinstance(value, UnitCombatState):
        return value.value
    if isinstance(value, str) and value:
        lowered = value.strip().lower()
        if lowered in _TRANSITIONS:
            return lowered
    return UnitCombatState.IDLE.value
