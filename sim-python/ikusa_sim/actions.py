"""Combat action skeleton for the formalized runtime architecture."""

from dataclasses import dataclass, field
from itertools import count
from typing import Callable, List, Optional

from ikusa_sim.events import BattleEvent


_ACTION_COUNTER = count(1)


@dataclass(frozen=True)
class CombatAction:
    action_id: str
    unit_id: str
    action_type: str
    target_id: Optional[str]
    tick: int
    reason: str


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    events: List[BattleEvent] = field(default_factory=list)
    reason: str = ""


def build_basic_attack_action(
    unit_id: str,
    target_id: Optional[str],
    tick: int,
    reason: str,
) -> CombatAction:
    return CombatAction(
        action_id=_next_action_id(unit_id, tick, "basic_attack"),
        unit_id=unit_id,
        action_type="basic_attack",
        target_id=target_id,
        tick=tick,
        reason=reason,
    )


def build_skill_action(
    unit_id: str,
    skill_id: Optional[str],
    target_id: Optional[str],
    tick: int,
    reason: str,
) -> CombatAction:
    action_reason = reason if not skill_id else f"{reason}:{skill_id}"
    return CombatAction(
        action_id=_next_action_id(unit_id, tick, "skill"),
        unit_id=unit_id,
        action_type="skill",
        target_id=target_id,
        tick=tick,
        reason=action_reason,
    )


def validate_combat_action(action: CombatAction) -> ActionResult:
    if not action.unit_id:
        return ActionResult(ok=False, reason="missing unit_id")
    if action.action_type not in {"basic_attack", "skill"}:
        return ActionResult(ok=False, reason=f"unsupported action_type: {action.action_type}")
    if action.target_id is None and action.action_type == "basic_attack":
        return ActionResult(ok=False, reason="missing target_id")
    return ActionResult(ok=True, reason="validated")


def resolve_combat_action(
    action: CombatAction,
    *,
    basic_attack_handler: Optional[Callable[[CombatAction], ActionResult]] = None,
    skill_handler: Optional[Callable[[CombatAction], ActionResult]] = None,
) -> ActionResult:
    validation = validate_combat_action(action)
    if not validation.ok:
        return validation

    if action.action_type == "basic_attack":
        if basic_attack_handler is not None:
            result = basic_attack_handler(action)
            if result is not None:
                return result
        return ActionResult(ok=True, reason="basic attack pipeline skeleton")

    if action.action_type == "skill":
        if skill_handler is not None:
            result = skill_handler(action)
            if result is not None:
                return result
        return ActionResult(ok=True, reason="skill pipeline skeleton")

    return ActionResult(ok=False, reason=f"unsupported action_type: {action.action_type}")


def _next_action_id(unit_id: str, tick: int, action_type: str) -> str:
    return f"action_{tick:06d}_{unit_id}_{action_type}_{next(_ACTION_COUNTER):04d}"
