"""Minimal skill trigger resolver for Ikusa Forge Phase 1.

This module uses a fixed handler map for sample skills. It intentionally does not
implement a general-purpose skill DSL, synergies, formation bonuses,
battle reports, viewers, host integration, or Godot logic.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Mapping, Optional, Sequence

from ikusa_sim.combat_rules import (
    apply_damage,
    attack_interval_to_ticks,
    calculate_skill_damage,
)
from ikusa_sim.events import BattleEvent
from ikusa_sim.models import ConfigBundle, SkillDef
from ikusa_sim.runtime_models import BattleState, UnitState
from ikusa_sim.targeting import TargetDecision


@dataclass(frozen=True)
class SkillUseResult:
    used: bool
    damaged_targets: List[UnitState]
    target_reason: Optional[str] = None
    target_score: Optional[Mapping[str, int]] = None


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


def mark_skill_used(unit: UnitState, skill: SkillDef, tick: int, tick_rate: int) -> None:
    unit.skill_cooldowns[skill.id] = tick + attack_interval_to_ticks(skill.cooldown, tick_rate)


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
            if result.used:
                mark_skill_used(unit, skill, tick, state.tick_rate)


def try_use_on_attack_skill(
    attacker: UnitState,
    target: UnitState,
    state: BattleState,
    config: ConfigBundle,
    tick: int,
    events: List[BattleEvent],
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
        )
        if result.used:
            mark_skill_used(attacker, skill, tick, state.tick_rate)
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
        )
        if result.used:
            mark_skill_used(defender, skill, tick, state.tick_rate)
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
            )
            if result.used:
                mark_skill_used(reactor, skill, tick, state.tick_rate)
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
) -> SkillUseResult:
    _ = current_target
    _ = config
    _ = tick
    source.guard_value += int(round(skill.effect_value))
    _emit_skill_trigger(
        state,
        events,
        tick,
        source,
        skill,
        [source],
        target_reason,
        target_score,
    )
    return SkillUseResult(used=True, damaged_targets=[])


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
) -> SkillUseResult:
    _ = current_target
    _ = config
    targets = _adjacent_allies(source, state.units)
    if not targets:
        return SkillUseResult(used=False, damaged_targets=[])

    bonus = int(round(skill.effect_value))
    for target in targets:
        target.atk += bonus
    _emit_skill_trigger(
        state,
        events,
        tick,
        source,
        skill,
        targets,
        target_reason,
        target_score,
    )
    return SkillUseResult(used=True, damaged_targets=[])


def _resolve_damage_skill(
    source: UnitState,
    skill: SkillDef,
    targets: Sequence[UnitState],
    state: BattleState,
    tick: int,
    events: List[BattleEvent],
    target_reason: Optional[str],
    target_score: Optional[Mapping[str, int]],
) -> SkillUseResult:
    live_targets = [target for target in targets if target.alive]
    if not live_targets:
        return SkillUseResult(used=False, damaged_targets=[])

    _emit_skill_trigger(
        state,
        events,
        tick,
        source,
        skill,
        live_targets,
        target_reason,
        target_score,
    )
    damaged_targets = []  # type: List[UnitState]
    for target in live_targets:
        amount = calculate_skill_damage(source, target, skill)
        reason = f"skill:{skill.id}"
        died = apply_damage(target, amount, reason=reason, source=source.instance_id)
        events.append(
            BattleEvent(
                tick=tick,
                event_id=_next_event_id(state),
                type="damage",
                payload={
                    "source": source.instance_id,
                    "target": target.instance_id,
                    "amount": amount,
                    "target_hp_after": target.hp,
                    "reason": reason,
                },
            )
        )
        damaged_targets.append(target)
        if died:
            events.append(
                BattleEvent(
                    tick=tick,
                    event_id=_next_event_id(state),
                    type="death",
                    payload={"unit": target.instance_id},
                )
            )
    return SkillUseResult(
        used=True,
        damaged_targets=damaged_targets,
        target_reason=target_reason,
        target_score=target_score,
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
