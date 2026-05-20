"""Status lifecycle helpers for the combat runtime."""

from dataclasses import asdict
from typing import List, Optional

from ikusa_sim.effect_models import StatusApplyEffect, StatusExpireEffect
from ikusa_sim.runtime_models import BattleState, StatusEffect, UnitState


def apply_status_effect(unit: UnitState, effect: StatusApplyEffect, *, tick: int) -> None:
    status = StatusEffect(
        id=effect.status_id,
        source=effect.source,
        source_type="skill",
        target=effect.target,
        stat=effect.stat,
        amount=effect.amount,
        start_tick=tick,
        expire_tick=effect.expire_tick,
        reason=effect.reason,
    )
    unit.statuses.append(status)
    _apply_stat_delta(unit, effect.stat, effect.amount)


def build_status_expire_effects(state: BattleState, tick: int) -> List[StatusExpireEffect]:
    effects: List[StatusExpireEffect] = []
    for unit_id in sorted(unit.instance_id for unit in state.units if unit.statuses):
        unit = _find_unit(state, unit_id)
        if unit is None:
            continue
        for status in _expired_statuses(unit, tick):
            effects.append(
                StatusExpireEffect(
                    status_id=status.id,
                    target=unit.instance_id,
                    stat=status.stat,
                    amount=status.amount,
                    reason=f"status_expired:{status.id}",
                )
            )
    return effects


def apply_status_expire_effect(state: BattleState, effect: StatusExpireEffect) -> Optional[StatusEffect]:
    unit = _find_unit(state, effect.target)
    if unit is None:
        return None
    status = _find_status(unit, effect.status_id)
    if status is None:
        return None
    _rollback_stat_delta(unit, status.stat, status.amount)
    unit.statuses.remove(status)
    return status


def emit_status_expire_event(
    tick: int,
    effect: StatusExpireEffect,
):
    return {
        "type": "status_expire",
        "payload": asdict(effect),
        "tick": tick,
    }


def expire_status_effects(state: BattleState, tick: int) -> List[StatusEffect]:
    return _remove_expired_statuses(state, tick)


def _expired_statuses(unit: UnitState, tick: int) -> List[StatusEffect]:
    return sorted(
        [status for status in unit.statuses if status.expire_tick is not None and status.expire_tick <= tick],
        key=lambda status: (status.id,),
    )


def _remove_expired_statuses(state: BattleState, tick: int) -> List[StatusEffect]:
    expired: List[StatusEffect] = []
    for unit in sorted(state.units, key=lambda unit: unit.instance_id):
        removable = _expired_statuses(unit, tick)
        for status in removable:
            _rollback_stat_delta(unit, status.stat, status.amount)
            unit.statuses.remove(status)
            expired.append(status)
    return expired


def _apply_stat_delta(unit: UnitState, stat: str, amount: int) -> None:
    if stat == "atk":
        unit.atk += amount
    elif stat == "guard_value":
        unit.guard_value += amount


def _rollback_stat_delta(unit: UnitState, stat: str, amount: int) -> None:
    if stat == "atk":
        unit.atk -= amount
    elif stat == "guard_value":
        unit.guard_value -= amount


def _find_status(unit: UnitState, status_id: str) -> Optional[StatusEffect]:
    for status in unit.statuses:
        if status.id == status_id:
            return status
    return None


def _find_unit(state: BattleState, unit_id: str) -> Optional[UnitState]:
    for unit in state.units:
        if unit.instance_id == unit_id:
            return unit
    return None
