"""Deterministic targeting rules for basic combat."""

from typing import List, Optional, Sequence, Tuple

from ikusa_sim.runtime_models import UnitState


def select_target(attacker: UnitState, candidates: Sequence[UnitState]) -> Optional[UnitState]:
    enemies = _alive_enemies(attacker, candidates)
    if not enemies:
        return None

    exposed = _filter_by_exposure(attacker, enemies)
    if not exposed:
        return None

    scored = [
        (_target_score(attacker, target), _hp_ratio(target), target)
        for target in exposed
    ]
    scored.sort(key=lambda item: (-item[0], item[1], item[2].instance_id))
    return scored[0][2]


def _alive_enemies(attacker: UnitState, candidates: Sequence[UnitState]) -> List[UnitState]:
    return [
        candidate
        for candidate in candidates
        if candidate.alive and candidate.side != attacker.side
    ]


def _filter_by_exposure(attacker: UnitState, enemies: Sequence[UnitState]) -> List[UnitState]:
    layers = sorted({enemy.y for enemy in enemies})
    if not layers:
        return []

    attack_range = max(1, attacker.base_range)
    layer_count = attack_range if attack_range < 3 else len(layers)
    allowed_layers = set(layers[:layer_count])
    return [enemy for enemy in enemies if enemy.y in allowed_layers]


def _target_score(attacker: UnitState, target: UnitState) -> float:
    score = 0.0
    column_delta = abs(attacker.x - target.x)
    if column_delta == 0:
        score += 100.0
    elif column_delta == 1:
        score += 50.0

    score += (1.0 - _hp_ratio(target)) * 10.0
    return score


def _hp_ratio(unit: UnitState) -> float:
    if unit.base_hp <= 0:
        return 0.0
    return float(unit.hp) / float(unit.base_hp)
