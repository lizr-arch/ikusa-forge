"""Basic attack and damage rules for Ikusa Forge Phase 1."""

from typing import Optional

from ikusa_sim.models import SkillDef
from ikusa_sim.runtime_models import UnitState


def attack_interval_to_ticks(attack_interval: float, tick_rate: int) -> int:
    ticks = int(round(attack_interval * tick_rate))
    return max(1, ticks)


def calculate_basic_damage(attacker: UnitState, defender: UnitState) -> int:
    return _calculate_damage(attacker.atk, defender)


def calculate_skill_damage(attacker: UnitState, defender: UnitState, skill: SkillDef) -> int:
    return _calculate_damage(attacker.atk + int(round(skill.effect_value)), defender)


def apply_damage(
    defender: UnitState,
    amount: int,
    reason: Optional[str] = None,
    source: Optional[str] = None,
) -> bool:
    _ = reason
    _ = source
    if not defender.alive:
        return False

    defender.hp = max(0, defender.hp - max(0, amount))
    if defender.hp > 0:
        return False

    defender.alive = False
    return True


def _calculate_damage(raw_power: int, defender: UnitState) -> int:
    mitigation = defender.defense + defender.guard_value
    return max(1, raw_power - mitigation)
