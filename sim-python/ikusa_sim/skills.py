"""Minimal skill trigger resolver for Ikusa Forge Phase 1.

This module uses a fixed handler map for sample skills. It intentionally does not
implement a general-purpose skill DSL, synergies, formation bonuses,
battle reports, viewers, host integration, or Godot logic.
"""

from dataclasses import asdict, dataclass, field
from typing import Callable, Dict, List, Mapping, Optional, Sequence

from ikusa_sim.action_pipeline import build_skill_action, run_combat_action
from ikusa_sim.combat_rules import attack_interval_to_ticks, calculate_skill_damage
from ikusa_sim.events import BattleEvent
from ikusa_sim.models import ConfigBundle, SkillDef
from ikusa_sim.runtime_models import BattleState, StatusEffect, UnitState
from ikusa_sim.targeting import TargetDecision


@dataclass(frozen=True)
class SkillUseResult:
    used: bool
    damaged_targets: List[UnitState]
    target_reason: Optional[str] = None
    target_score: Optional[Mapping[str, int]] = None
    cooldown_handled: bool = False


SkillHandler = Callable[
    [
        UnitState,
        Optional[UnitState],
        BattleState,
        ConfigBundle,
        int,
        List[BattleEvent],
        SkillDef,
        Optional[str],
        Optional[Mapping[str, int]],
        bool,
    ],
    SkillUseResult,
]


def get_ready_skills(
    unit: UnitState,
    config: ConfigBundle,
    trigger: str,
    tick: int,
) -> List[SkillDef]:
    ready = []  # type: List[SkillDef]
    for skill_id in unit.skill_ids:
        skill = config.skills.get(skill_id)
        if skill is None or skill.trigger != trigger:
            continue
        if unit.skill_cooldowns.get(skill.id, 0) <= tick:
            ready.append(skill)
    return ready


def mark_skill_used(unit: UnitState, skill: SkillDef, tick: int, tick_rate: int) -> int:
    ready_tick = tick + attack_interval_to_ticks(skill.cooldown, tick_rate)
    unit.skill_cooldowns[skill.id] = ready_tick
    return ready_tick


def try_use_on_battle_start_skills(
    state: BattleState,
    config: ConfigBundle,
    events: List[BattleEvent],
) -> None:
    tick = state.current_tick
    for unit in state.units:
        if not unit.alive:
            continue
        for skill in get_ready_skills(unit, config, "on_battle_start", tick):
            result = _use_skill(
                unit,
                None,
                state,
                config,
                tick,
                events,
                skill,
                _derive_skill_target_reason(skill),
                None,
            )


def try_use_on_attack_skill(
    attacker: UnitState,
    target: UnitState,
    state: BattleState,
    config: ConfigBundle,
    tick: int,
    events: List[BattleEvent],
    schedule_next_action: bool = False,
    target_decision: Optional[TargetDecision] = None,
) -> SkillUseResult:
    if not attacker.alive:
        return SkillUseResult(used=False, damaged_targets=[])

    for skill in get_ready_skills(attacker, config, "on_attack", tick):
        reason = _derive_skill_target_reason(skill)
        score_payload = _target_score_payload(target_decision)
        # 当前目标类技能保留 winner 决策评分，便于后续解释；非当前目标技能通常使用自定义选择逻辑。
        if reason != "current_target":
            score_payload = None
        result = _use_skill(
            attacker,
            target,
            state,
            config,
            tick,
            events,
            skill,
            reason,
            score_payload,
            schedule_next_action,
        )
        if result.used:
            return result
    return SkillUseResult(used=False, damaged_targets=[])


def try_use_on_attacked_skills(
    attacker: UnitState,
    defender: UnitState,
    state: BattleState,
    config: ConfigBundle,
    tick: int,
    events: List[BattleEvent],
) -> None:
    if not attacker.alive or not defender.alive:
        return

    for skill in get_ready_skills(defender, config, "on_attacked", tick):
        reason = _derive_skill_target_reason(skill)
        result = _use_skill(
            defender,
            attacker,
            state,
            config,
            tick,
            events,
            skill,
            reason,
            None,
            False,
        )
        if not attacker.alive:
            return


def try_use_on_ally_attacked_skills(
    attacker: UnitState,
    defender: UnitState,
    state: BattleState,
    config: ConfigBundle,
    tick: int,
    events: List[BattleEvent],
) -> None:
    if not attacker.alive:
        return

    reactors = [
        unit
        for unit in state.units
        if unit.alive
        and unit.side == defender.side
        and unit.instance_id != defender.instance_id
    ]
    reactors.sort(key=lambda unit: unit.instance_id)

    for reactor in reactors:
        for skill in get_ready_skills(reactor, config, "on_ally_attacked", tick):
            result = _use_skill(
                reactor,
                attacker,
                state,
                config,
                tick,
                events,
                skill,
                _derive_skill_target_reason(skill),
                None,
                False,
            )
        if not attacker.alive:
            return


def _use_skill(
    source: UnitState,
    current_target: Optional[UnitState],
    state: BattleState,
    config: ConfigBundle,
    tick: int,
    events: List[BattleEvent],
    skill: SkillDef,
    target_reason: Optional[str] = None,
    target_score: Optional[Mapping[str, int]] = None,
    schedule_next_action: bool = False,
) -> SkillUseResult:
    handler = SKILL_HANDLERS.get(skill.id)
    if handler is None:
        return SkillUseResult(used=False, damaged_targets=[])
    return handler(
        source,
        current_target,
        state,
        config,
        tick,
        events,
        skill,
        target_reason,
        target_score,
        schedule_next_action,
    )


def _handle_current_target_damage(
    source: UnitState,
    current_target: Optional[UnitState],
    state: BattleState,
    config: ConfigBundle,
    tick: int,
    events: List[BattleEvent],
    skill: SkillDef,
    target_reason: Optional[str],
    target_score: Optional[Mapping[str, int]],
    schedule_next_action: bool,
) -> SkillUseResult:
    _ = config
    if current_target is None or not current_target.alive:
        return SkillUseResult(used=False, damaged_targets=[])
    return _resolve_damage_skill(
        source,
        skill,
        [current_target],
        state,
        tick,
        events,
        target_reason,
        target_score,
        schedule_next_action,
    )


def _handle_lowest_hp_enemy_damage(
    source: UnitState,
    current_target: Optional[UnitState],
    state: BattleState,
    config: ConfigBundle,
    tick: int,
    events: List[BattleEvent],
    skill: SkillDef,
    target_reason: Optional[str],
    target_score: Optional[Mapping[str, int]],
    schedule_next_action: bool,
) -> SkillUseResult:
    _ = current_target
    _ = config
    target = _lowest_hp_enemy(source, state.units)
    if target is None:
        return SkillUseResult(used=False, damaged_targets=[])
    return _resolve_damage_skill(
        source,
        skill,
        [target],
        state,
        tick,
        events,
        target_reason,
        target_score,
        schedule_next_action,
    )


def _handle_guard(
    source: UnitState,
    current_target: Optional[UnitState],
    state: BattleState,
    config: ConfigBundle,
    tick: int,
    events: List[BattleEvent],
    skill: SkillDef,
    target_reason: Optional[str],
    target_score: Optional[Mapping[str, int]],
    schedule_next_action: bool,
) -> SkillUseResult:
    _ = current_target
    _ = config
    action = build_skill_action(state, source, skill, [source], tick, target_reason, target_score)
    action.metadata["status_stat"] = "guard_value"
    action.metadata["status_amount"] = int(round(skill.effect_value))
    result = run_combat_action(state, action, tick, events, schedule_next_action=schedule_next_action)
    if not result.ok:
        return SkillUseResult(used=False, damaged_targets=[])
    return SkillUseResult(used=True, damaged_targets=[], cooldown_handled=True)


def _handle_banner_rally(
    source: UnitState,
    current_target: Optional[UnitState],
    state: BattleState,
    config: ConfigBundle,
    tick: int,
    events: List[BattleEvent],
    skill: SkillDef,
    target_reason: Optional[str],
    target_score: Optional[Mapping[str, int]],
    schedule_next_action: bool,
) -> SkillUseResult:
    _ = current_target
    _ = config
    targets = _adjacent_allies(source, state.units)
    if not targets:
        return SkillUseResult(used=False, damaged_targets=[])

    action = build_skill_action(state, source, skill, targets, tick, target_reason, target_score)
    action.metadata["status_stat"] = "atk"
    action.metadata["status_amount"] = int(round(skill.effect_value))
    result = run_combat_action(state, action, tick, events, schedule_next_action=schedule_next_action)
    if not result.ok:
        return SkillUseResult(used=False, damaged_targets=[])
    return SkillUseResult(used=True, damaged_targets=[], cooldown_handled=True)


def _resolve_damage_skill(
    source: UnitState,
    skill: SkillDef,
    targets: Sequence[UnitState],
    state: BattleState,
    tick: int,
    events: List[BattleEvent],
    target_reason: Optional[str],
    target_score: Optional[Mapping[str, int]],
    schedule_next_action: bool = False,
) -> SkillUseResult:
    live_targets = [target for target in targets if target.alive]
    if not live_targets:
        return SkillUseResult(used=False, damaged_targets=[])

    action = build_skill_action(state, source, skill, live_targets, tick, target_reason, target_score)
    action.metadata["effect_type"] = "damage"
    result = run_combat_action(state, action, tick, events, schedule_next_action=schedule_next_action)
    if not result.ok:
        return SkillUseResult(used=False, damaged_targets=[])

    return SkillUseResult(
        used=True,
        damaged_targets=live_targets,
        target_reason=target_reason,
        target_score=target_score,
        cooldown_handled=True,
    )


def _emit_skill_trigger(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    source: UnitState,
    skill: SkillDef,
    targets: Sequence[UnitState],
    target_reason: Optional[str],
    target_score: Optional[Mapping[str, int]],
) -> None:
    # Legacy fallback: kept for compatibility with older call sites.
    # Integrated runtime paths route through action_pipeline actions.
    payload: Dict[str, object] = {
        "source": source.instance_id,
        "skill": skill.id,
        "trigger": skill.trigger,
        "targets": [target.instance_id for target in targets],
    }
    if target_reason is not None:
        payload["target_reason"] = target_reason
    if target_score is not None:
        payload["target_score"] = dict(target_score)

    events.append(
        BattleEvent(
            tick=tick,
            event_id=_next_event_id(state),
            type="skill_trigger",
            payload=payload,
        )
    )


def _apply_status(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    source: UnitState,
    target: UnitState,
    skill: SkillDef,
    *,
    stat: str,
    amount: int,
    target_reason: Optional[str],
) -> None:
    # Legacy fallback: kept for compatibility with older offline helpers.
    # Integrated runtime paths apply status through action_pipeline + status_system.
    status = StatusEffect(
        id=_status_id(target, skill),
        source=source.instance_id,
        source_type="skill",
        target=target.instance_id,
        stat=stat,
        amount=amount,
        start_tick=tick,
        expire_tick=None,
        reason=f"skill:{skill.id}",
    )
    target.statuses.append(status)

    payload: Dict[str, object] = asdict(status)
    if target_reason is not None:
        payload["target_reason"] = target_reason

    events.append(
        BattleEvent(
            tick=tick,
            event_id=_next_event_id(state),
            type="status_apply",
            payload=payload,
        )
    )


def _mark_skill_used_and_emit_cooldown(
    unit: UnitState,
    skill: SkillDef,
    state: BattleState,
    tick: int,
    events: List[BattleEvent],
) -> None:
    # Legacy fallback: used only when bypassing action_pipeline.
    # Preferred path is pipeline-generated CooldownEffect.
    ready_tick = mark_skill_used(unit, skill, tick, state.tick_rate)
    events.append(
        BattleEvent(
            tick=tick,
            event_id=_next_event_id(state),
            type="skill_cooldown",
            payload={
                "source": unit.instance_id,
                "skill": skill.id,
                "start_tick": tick,
                "ready_tick": ready_tick,
                "cooldown_ticks": ready_tick - tick,
            },
        )
    )


def _status_id(target: UnitState, skill: SkillDef) -> str:
    return f"status_{target.instance_id}_{skill.id}_{len(target.statuses) + 1:03d}"


def _lowest_hp_enemy(source: UnitState, units: Sequence[UnitState]) -> Optional[UnitState]:
    enemies = [
        unit
        for unit in units
        if unit.alive and unit.side != source.side
    ]
    if not enemies:
        return None
    enemies.sort(key=lambda unit: (_hp_ratio(unit), unit.hp, unit.instance_id))
    return enemies[0]


def _adjacent_allies(source: UnitState, units: Sequence[UnitState]) -> List[UnitState]:
    allies = [
        unit
        for unit in units
        if unit.alive
        and unit.side == source.side
        and unit.instance_id != source.instance_id
        and abs(unit.x - source.x) <= 1
        and abs(unit.y - source.y) <= 1
    ]
    allies.sort(key=lambda unit: unit.instance_id)
    return allies


def _derive_skill_target_reason(
    skill: SkillDef,
) -> str:
    if skill.target_rule == "lowest_hp_enemy":
        return "lowest_hp_enemy"
    if skill.target_rule == "current_target":
        return "current_target"
    if skill.target_rule == "attacker":
        return "current_target"
    if skill.target_rule == "adjacent_allies":
        return "adjacent_allies"
    if skill.target_rule == "self":
        return "self"
    return "current_target"


def _target_score_payload(
    target_decision: Optional[TargetDecision],
) -> Optional[Mapping[str, int]]:
    if target_decision is None or target_decision.score is None:
        return None
    score = target_decision.score
    return {
        "final": score.final_score,
        "exposure": score.exposure_score,
        "column": score.column_score,
        "low_hp": score.low_hp_score,
        "threat": score.threat_score,
        "role": score.role_score,
        "tie_break": score.tie_break,
    }


def _hp_ratio(unit: UnitState) -> float:
    if unit.base_hp <= 0:
        return 0.0
    return float(unit.hp) / float(unit.base_hp)


def _format_event_id(sequence_number: int) -> str:
    return f"evt_{sequence_number:06d}"


def _next_event_id(state: BattleState) -> str:
    event_id = _format_event_id(state._next_event_number)
    state._next_event_number += 1
    return event_id


SKILL_HANDLERS = {
    "katana_slash": _handle_current_target_damage,
    "iaijutsu_burst": _handle_lowest_hp_enemy_damage,
    "spear_thrust": _handle_current_target_damage,
    "brace_counter": _handle_current_target_damage,
    "bow_shot": _handle_current_target_damage,
    "focus_fire": _handle_lowest_hp_enemy_damage,
    "shield_guard": _handle_guard,
    "intercept": _handle_current_target_damage,
    "smoke_strike": _handle_current_target_damage,
    "banner_rally": _handle_banner_rally,
}  # type: Dict[str, SkillHandler]
