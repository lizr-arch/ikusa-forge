from dataclasses import asdict
from typing import Dict, List, Mapping, Optional, Sequence

from ikusa_sim.actions import (
    ActionResult,
    CombatAction,
    build_basic_attack_action as _build_basic_attack_action,
    build_skill_action as _build_skill_action,
)
from ikusa_sim.combat_rules import (
    apply_damage,
    attack_interval_to_ticks,
    calculate_basic_damage,
    calculate_skill_damage,
)
from ikusa_sim.effect_models import (
    ActionScheduleEffect,
    CooldownEffect,
    DamageEffect,
    DeathEffect,
    Effect,
    StatusExpireEffect,
    StatusApplyEffect,
)
from ikusa_sim.events import BattleEvent
from ikusa_sim.models import SkillDef
from ikusa_sim.runtime_models import BattleState, UnitState
from ikusa_sim.status_system import apply_status_effect, apply_status_expire_effect
from ikusa_sim.spatial_utils import distance_between


def _find_unit(state: BattleState, unit_id: str) -> Optional[UnitState]:
    for unit in state.units:
        if unit.instance_id == unit_id:
            return unit
    return None


def build_basic_attack_action(
    state: BattleState,
    attacker: UnitState,
    target: Optional[UnitState],
    tick: int,
) -> CombatAction:
    target_id = target.instance_id if target is not None else None
    return _build_basic_attack_action(
        unit_id=attacker.instance_id,
        target_id=target_id,
        tick=tick,
        reason="spatial_engaged_target",
    )


def build_skill_action(
    state: BattleState,
    source: UnitState,
    skill: SkillDef,
    targets: Sequence[UnitState],
    tick: int,
    target_reason: Optional[str] = None,
    target_score: Optional[Mapping[str, int]] = None,
) -> CombatAction:
    cooldown_ticks = attack_interval_to_ticks(skill.cooldown, state.tick_rate)

    target_id = targets[0].instance_id if targets else None

    effect_type = "damage" if skill.effect_type == "damage" else "status"

    metadata: Dict[str, object] = {
        "target_ids": [t.instance_id for t in targets],
        "effect_type": effect_type,
        "trigger": skill.trigger,
        "skill_id": skill.id,
        "cooldown_ticks": cooldown_ticks,
        "effect_value": skill.effect_value,
    }
    if target_reason is not None:
        metadata["target_reason"] = target_reason
    if target_score is not None:
        metadata["target_score"] = dict(target_score)

    action = _build_skill_action(
        unit_id=source.instance_id,
        skill_id=skill.id,
        target_id=target_id,
        tick=tick,
        reason=f"skill:{skill.id}",
    )
    action.metadata.update(metadata)
    return action


def validate_combat_action(state: BattleState, action: CombatAction) -> ActionResult:
    if not action.unit_id:
        return ActionResult(ok=False, reason="missing unit_id")

    attacker = _find_unit(state, action.unit_id)
    if attacker is None or not attacker.alive:
        return ActionResult(ok=False, reason=f"unit not found or dead: {action.unit_id}")

    if action.action_type not in {"basic_attack", "skill"}:
        return ActionResult(ok=False, reason=f"unsupported action_type: {action.action_type}")

    if action.action_type == "basic_attack":
        if action.target_id is None:
            return ActionResult(ok=False, reason="missing target_id")
        target = _find_unit(state, action.target_id)
        if target is None or not target.alive:
            return ActionResult(ok=False, reason=f"target not found or dead: {action.target_id}")
        if distance_between(attacker, target) > attacker.attack_range + 0.001:
            return ActionResult(ok=False, reason="target out of attack_range")

    if action.action_type == "skill":
        if action.skill_id is not None:
            if attacker.skill_cooldowns.get(action.skill_id, 0) > state.current_tick:
                return ActionResult(
                    ok=False,
                    reason=f"skill on cooldown: {action.skill_id}",
                )
        if action.target_id is not None:
            target = _find_unit(state, action.target_id)
            if target is None or not target.alive:
                return ActionResult(ok=False, reason=f"target not found or dead: {action.target_id}")

    if state.finished:
        return ActionResult(ok=False, reason="battle already finished")

    return ActionResult(ok=True, reason="validated")


def resolve_combat_action(state: BattleState, action: CombatAction) -> ActionResult:
    validation = validate_combat_action(state, action)
    if not validation.ok:
        return validation

    if action.action_type == "basic_attack":
        attacker = _find_unit(state, action.unit_id)
        target = _find_unit(state, action.target_id) if action.target_id else None
        if attacker is None or target is None:
            return ActionResult(ok=False, reason="attacker or target not found")
        amount = calculate_basic_damage(attacker, target)
        return ActionResult(
            ok=True,
            reason="basic_attack_resolved",
            effects=[DamageEffect(source=attacker.instance_id, target=target.instance_id, amount=amount, reason="basic_attack")],
        )

    if action.action_type == "skill":
        source = _find_unit(state, action.unit_id)
        if source is None:
            return ActionResult(ok=False, reason="skill source not found")

        metadata = action.metadata
        target_ids = metadata.get("target_ids", [])
        effect_type = metadata.get("effect_type", "damage")
        skill_id = metadata.get("skill_id", action.skill_id or "unknown")
        cooldown_ticks = metadata.get("cooldown_ticks", 0)

        effects: List[object] = []

        if effect_type == "damage":
            skill_def_data = {"id": skill_id, "effect_value": float(metadata.get("effect_value", 0))}
            skill_def = SkillDef(
                id=str(skill_def_data["id"]),
                name=str(skill_def_data["id"]),
                trigger=str(metadata.get("trigger", "on_attack")),
                target_rule="current_target",
                cooldown=0.0,
                effect_type="damage",
                effect_value=skill_def_data["effect_value"],
                tags=[],
            )
            for target_id in target_ids:
                if not isinstance(target_id, str):
                    continue
                target = _find_unit(state, target_id)
                if target is None or not target.alive:
                    continue
                amount = calculate_skill_damage(source, target, skill_def)
                effects.append(
                    DamageEffect(
                        source=source.instance_id,
                        target=target.instance_id,
                        amount=amount,
                        reason=f"skill:{skill_id}",
                    )
                )

        elif effect_type == "status":
            status_stat = str(metadata.get("status_stat", "atk"))
            status_amount = int(metadata.get("status_amount", int(float(str(metadata.get("effect_value", 0))))))
            for target_id in target_ids:
                if not isinstance(target_id, str):
                    continue
                target = _find_unit(state, target_id)
                if target is None or not target.alive:
                    continue
                effects.append(
                    StatusApplyEffect(
                        source=source.instance_id,
                        target=target.instance_id,
                        status_id=_make_status_id(target, skill_id),
                        stat=status_stat,
                        amount=status_amount,
                        expire_tick=None,
                        reason=f"skill:{skill_id}",
                    )
                )

        skill_id_str = str(skill_id)
        cooldown_ticks_int = int(cooldown_ticks) if isinstance(cooldown_ticks, (int, float)) else 0
        if cooldown_ticks_int > 0:
            effects.append(
                CooldownEffect(
                    source=source.instance_id,
                    skill_id=skill_id_str,
                    start_tick=state.current_tick,
                    ready_tick=state.current_tick + cooldown_ticks_int,
                    cooldown_ticks=cooldown_ticks_int,
                )
            )

        return ActionResult(ok=True, reason="skill_resolved", effects=effects)

    return ActionResult(ok=False, reason=f"unsupported action_type: {action.action_type}")


def apply_effects(state: BattleState, effects: Sequence[Effect], tick: int) -> bool:
    any_death = False

    for effect in effects:
        if isinstance(effect, DamageEffect):
            target = _find_unit(state, effect.target)
            if target is not None and target.alive:
                died = apply_damage(target, effect.amount, reason=effect.reason, source=effect.source)
                if died:
                    any_death = True

        elif isinstance(effect, StatusApplyEffect):
            target = _find_unit(state, effect.target)
            if target is not None and target.alive:
                apply_status_effect(target, effect, tick=tick)

        elif isinstance(effect, CooldownEffect):
            source = _find_unit(state, effect.source)
            if source is not None:
                source.skill_cooldowns[effect.skill_id] = effect.ready_tick

        elif isinstance(effect, DeathEffect):
            unit = _find_unit(state, effect.unit)
            if unit is not None:
                unit.alive = False
                any_death = True

        elif isinstance(effect, ActionScheduleEffect):
            unit = _find_unit(state, effect.unit)
            if unit is not None:
                unit.next_action_tick = effect.next_action_tick

        elif isinstance(effect, StatusExpireEffect):
            apply_status_expire_effect(state, effect)

    return any_death


def emit_events_from_effects(
    state: BattleState,
    action: CombatAction,
    effects: Sequence[Effect],
    tick: int,
    events: List[BattleEvent],
) -> None:
    if action.action_type == "basic_attack":
        payload: Dict[str, object] = {
            "attacker": action.unit_id,
            "target": action.target_id or "",
            "target_reason": action.reason,
        }
        if "target_reason" in action.metadata:
            payload["target_reason"] = action.metadata["target_reason"]
        if "target_score" in action.metadata:
            payload["target_score"] = action.metadata["target_score"]
        events.append(
            BattleEvent(
                tick=tick,
                event_id=_next_event_id(state),
                type="attack",
                payload=payload,
            )
        )

    elif action.action_type == "skill":
        skill_payload: Dict[str, object] = {
            "source": action.unit_id,
            "skill": action.skill_id or "",
            "trigger": action.metadata.get("trigger", "on_attack"),
            "targets": action.metadata.get("target_ids", []),
        }
        if "target_reason" in action.metadata:
            skill_payload["target_reason"] = action.metadata["target_reason"]
        if "target_score" in action.metadata:
            skill_payload["target_score"] = action.metadata["target_score"]
        events.append(
            BattleEvent(
                tick=tick,
                event_id=_next_event_id(state),
                type="skill_trigger",
                payload=skill_payload,
            )
        )

    for effect in effects:
        if isinstance(effect, DamageEffect):
            target = _find_unit(state, effect.target)
            events.append(
                BattleEvent(
                    tick=tick,
                    event_id=_next_event_id(state),
                    type="damage",
                    payload={
                        "source": effect.source,
                        "target": effect.target,
                        "amount": effect.amount,
                        "target_hp_after": target.hp if target is not None else 0,
                        "reason": effect.reason,
                    },
                )
            )
            if target is not None and not target.alive:
                events.append(
                    BattleEvent(
                        tick=tick,
                        event_id=_next_event_id(state),
                        type="death",
                        payload={"unit": effect.target},
                    )
                )

        elif isinstance(effect, StatusApplyEffect):
            target = _find_unit(state, effect.target)
            if target is not None:
                status_payload: Dict[str, object] = {
                    "id": effect.status_id,
                    "source": effect.source,
                    "source_type": "skill",
                    "target": effect.target,
                    "stat": effect.stat,
                    "amount": effect.amount,
                    "start_tick": tick,
                    "expire_tick": effect.expire_tick,
                    "reason": effect.reason,
                }
                if "target_reason" in action.metadata:
                    status_payload["target_reason"] = action.metadata["target_reason"]
                events.append(
                    BattleEvent(
                        tick=tick,
                        event_id=_next_event_id(state),
                        type="status_apply",
                        payload=status_payload,
                    )
                )

        elif isinstance(effect, CooldownEffect):
            events.append(
                BattleEvent(
                    tick=tick,
                    event_id=_next_event_id(state),
                    type="skill_cooldown",
                    payload={
                        "source": effect.source,
                        "skill": effect.skill_id,
                        "start_tick": effect.start_tick,
                        "ready_tick": effect.ready_tick,
                        "cooldown_ticks": effect.cooldown_ticks,
                    },
                )
            )

        elif isinstance(effect, DeathEffect):
            events.append(
                BattleEvent(
                    tick=tick,
                    event_id=_next_event_id(state),
                    type="death",
                    payload={"unit": effect.unit},
                )
            )

        elif isinstance(effect, ActionScheduleEffect):
            events.append(
                BattleEvent(
                    tick=tick,
                    event_id=_next_event_id(state),
                    type="action_scheduled",
                    payload={
                        "unit": effect.unit,
                        "current_tick": effect.current_tick,
                        "next_action_tick": effect.next_action_tick,
                        "action_interval_ticks": effect.action_interval_ticks,
                        "reason": effect.reason,
                    },
                )
            )
        elif isinstance(effect, StatusExpireEffect):
            events.append(
                BattleEvent(
                    tick=tick,
                    event_id=_next_event_id(state),
                    type="status_expire",
                    payload=asdict(effect),
                )
            )


def run_combat_action(
    state: BattleState,
    action: CombatAction,
    tick: int,
    events: List[BattleEvent],
    *,
    schedule_next_action: bool = False,
) -> ActionResult:
    result = resolve_combat_action(state, action)
    if not result.ok:
        return result
    if schedule_next_action:
        unit = _find_unit(state, action.unit_id)
        if unit is not None and unit.alive:
            action_interval = unit.action_interval_ticks or attack_interval_to_ticks(unit.base_attack_interval, state.tick_rate)
            result.effects.append(
                ActionScheduleEffect(
                    unit=unit.instance_id,
                    current_tick=tick,
                    next_action_tick=tick + action_interval,
                    action_interval_ticks=action_interval,
                    reason="after_action",
                )
            )
    apply_effects(state, result.effects, tick)
    emit_events_from_effects(state, action, result.effects, tick, events)
    return result


def _make_status_id(target: UnitState, skill_id: str) -> str:
    return f"status_{target.instance_id}_{skill_id}_{len(target.statuses) + 1:03d}"


def _format_event_id(sequence_number: int) -> str:
    return f"evt_{sequence_number:06d}"


def _next_event_id(state: BattleState) -> str:
    event_id = _format_event_id(state._next_event_number)
    state._next_event_number += 1
    return event_id
