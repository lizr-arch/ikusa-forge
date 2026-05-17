"""Deterministic targeting rules for basic combat."""

from dataclasses import dataclass
from typing import List, Optional, Sequence

from ikusa_sim.runtime_models import UnitState


@dataclass(frozen=True)
class TargetCandidateScore:
    unit_id: str
    final_score: int
    exposure_score: int
    column_score: int
    low_hp_score: int
    threat_score: int
    role_score: int
    tie_break: int


@dataclass(frozen=True)
class TargetDecision:
    target: Optional[UnitState]
    reason: str
    score: Optional[TargetCandidateScore]
    candidates: List[TargetCandidateScore]


def select_target(attacker: UnitState, candidates: Sequence[UnitState]) -> Optional[UnitState]:
    decision = select_target_decision(attacker, candidates)
    return decision.target


def select_target_decision(attacker: UnitState, candidates: Sequence[UnitState]) -> TargetDecision:
    enemies = _alive_enemies(attacker, candidates)
    if not enemies:
        return TargetDecision(target=None, reason="no_enemies", score=None, candidates=[])

    exposed = _filter_by_exposure(attacker, enemies)
    if not exposed:
        return TargetDecision(target=None, reason="no_exposed_enemies", score=None, candidates=[])

    candidates_scores: List[TargetCandidateScore] = []
    for index, target in enumerate(exposed):
        candidates_scores.append(_target_score_components(attacker, target, index))

    # Deterministic tie-break: final_score desc, hp_ratio asc, instance_id asc.
    candidates_scores.sort(
        key=lambda item: (
            -item.final_score,
            _hp_ratio_from_id(item.unit_id, exposed),
            item.unit_id,
        )
    )

    winner_score = candidates_scores[0]
    winner_unit = _unit_by_instance(winner_score.unit_id, exposed)
    reason = _target_reason(attacker, winner_unit)
    return TargetDecision(
        target=winner_unit,
        reason=reason,
        score=winner_score,
        candidates=candidates_scores,
    )


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


def _target_score_components(
    attacker: UnitState,
    target: UnitState,
    tie_break: int,
) -> TargetCandidateScore:
    exposure_score = _exposure_score(attacker, target)
    column_score = _column_score(attacker, target)
    low_hp_score = _low_hp_score(target)
    threat_score = _threat_score(target)
    role_score = _role_preference_score(attacker, target)
    final_score = exposure_score + column_score + low_hp_score + threat_score + role_score
    return TargetCandidateScore(
        unit_id=target.instance_id,
        final_score=final_score,
        exposure_score=exposure_score,
        column_score=column_score,
        low_hp_score=low_hp_score,
        threat_score=threat_score,
        role_score=role_score,
        tie_break=tie_break,
    )


def _exposure_score(attacker: UnitState, target: UnitState) -> int:
    column_delta = abs(attacker.x - target.x)
    if column_delta == 0:
        return 100
    if column_delta == 1:
        return 60
    return 0


def _column_score(attacker: UnitState, target: UnitState) -> int:
    delta = abs(attacker.x - target.x)
    if delta == 0:
        return 40
    if delta == 1:
        return 30
    return 0


def _low_hp_score(unit: UnitState) -> int:
    ratio = _hp_ratio(unit)
    return int((1.0 - ratio) * 120)


def _threat_score(unit: UnitState) -> int:
    score = unit.atk
    score += unit.range * 4
    if unit.skill_ids:
        score += 15
    if _is_support_or_banner(unit):
        score += 10
    return score


def _role_preference_score(attacker: UnitState, target: UnitState) -> int:
    mode = _attacker_preference_mode(attacker)
    if mode == "frontline":
        if target.role in {"vanguard", "center", "front_guard", "frontline"}:
            return 20
        return 5
    if mode == "backline":
        if target.role in {"backline", "support", "left_support", "right_support"}:
            return 24
        if _low_hp_ratio(target):
            return 12
        return 0
    if mode == "high_threat":
        return 18 if _threat_score(target) >= 30 else 0
    if mode == "flank":
        if target.role in {"backline", "support", "left_support", "right_support"}:
            return 20
        return 6
    return 0


def _attacker_preference_mode(attacker: UnitState) -> str:
    tags = set(attacker.tags)
    role = attacker.role
    if "spear" in tags or role in {"vanguard", "front_guard", "frontline", "frontline_front"}:
        return "frontline"
    if "bow" in tags or "katana" in tags:
        return "high_threat"
    if "ninja" in tags or role in {"left_flank", "right_flank", "flank"}:
        return "flank"
    if role in {"backline", "support", "left_support", "right_support"}:
        return "backline"
    return "default"


def _is_support_or_banner(unit: UnitState) -> bool:
    return "support" in unit.role or "banner" in unit.tags


def _target_reason(attacker: UnitState, target: Optional[UnitState]) -> str:
    if not target:
        return "target_selected"
    if attacker.role == "flank" and target.role in {"support", "left_support", "right_support", "backline"}:
        return "ninja_targeting_support"
    if _is_same_column(attacker, target):
        return "frontline_exposed_same_column"
    if _is_adjacent_column(attacker, target):
        return "frontline_exposed_adjacent_column"
    return "frontline_exposed_remote"


def _is_same_column(attacker: UnitState, target: UnitState) -> bool:
    return attacker.x == target.x


def _is_adjacent_column(attacker: UnitState, target: UnitState) -> bool:
    return abs(attacker.x - target.x) == 1


def _hp_ratio(unit: UnitState) -> float:
    if unit.base_hp <= 0:
        return 0.0
    return float(unit.hp) / float(unit.base_hp)


def _low_hp_ratio(unit: UnitState) -> bool:
    return _hp_ratio(unit) < 0.75


def _unit_by_instance(instance_id: str, units: Sequence[UnitState]) -> Optional[UnitState]:
    for unit in units:
        if unit.instance_id == instance_id:
            return unit
    return None


def _hp_ratio_from_id(instance_id: str, units: Sequence[UnitState]) -> float:
    unit = _unit_by_instance(instance_id, units)
    if unit is None:
        return 1.0
    return _hp_ratio(unit)
