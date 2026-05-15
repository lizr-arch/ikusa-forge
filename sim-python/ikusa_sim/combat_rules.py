"""Basic attack and damage rules for Ikusa Forge Phase 1."""

from ikusa_sim.runtime_models import UnitState


def attack_interval_to_ticks(attack_interval: float, tick_rate: int) -> int:
    ticks = int(round(attack_interval * tick_rate))
    return max(1, ticks)


def calculate_basic_damage(attacker: UnitState, defender: UnitState) -> int:
    return max(1, attacker.base_atk - defender.base_defense)


def apply_damage(defender: UnitState, amount: int) -> bool:
    defender.hp = max(0, defender.hp - amount)
    if defender.hp > 0:
        return False

    defender.alive = False
    return True
