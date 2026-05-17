"""Basic combat runner for Ikusa Forge Phase 1.

This module implements deterministic targeting, basic attack, minimal skill
triggers, damage, death, and victory checks. It intentionally does not
implement viewers, host, or Godot logic.
"""

from typing import List, Optional, Tuple

from ikusa_sim.battle_skeleton import (
    battle_result_to_dict,
    create_battle_state,
    spawn_units_from_encounter,
)
from ikusa_sim.combat_rules import (
    apply_damage,
    attack_interval_to_ticks,
    calculate_basic_damage,
)
from ikusa_sim.formation_bonus import apply_formation_bonuses
from ikusa_sim.events import BattleEvent
from ikusa_sim.models import ConfigBundle
from ikusa_sim.synergy import apply_synergies
from ikusa_sim.rng import BattleRng
from ikusa_sim.runtime_models import BattleResult, BattleState, UnitState
from ikusa_sim.skills import (
    try_use_on_ally_attacked_skills,
    try_use_on_attack_skill,
    try_use_on_attacked_skills,
    try_use_on_battle_start_skills,
)
from ikusa_sim.targeting import TargetDecision, select_target_decision


def run_basic_combat(
    config: ConfigBundle,
    battle_id: str,
    seed: int,
) -> Tuple[BattleState, List[BattleEvent]]:
    if battle_id not in config.encounters:
        raise ValueError(f"Unknown encounter battle_id: {battle_id}")

    rng = BattleRng(seed)
    _ = rng

    state = create_battle_state(config, battle_id, seed)
    encounter = config.encounters[battle_id]
    events = [_battle_start_event(state)]
    events.extend(spawn_units_from_encounter(config, encounter, state))
    apply_formation_bonuses(state, events)
    apply_synergies(state, config, events)
    try_use_on_battle_start_skills(state, config, events)
    _initialize_action_schedule(state)

    for tick in range(0, state.max_ticks + 1):
        state.current_tick = tick
        result = _run_tick(state, config, events, tick)
        if result:
            _finish_battle(state, events, result)
            return state, events

    timeout = BattleResult(winner="draw", reason="timeout", end_tick=state.max_ticks)
    _finish_battle(state, events, timeout)
    return state, events


def _run_tick(
    state: BattleState,
    config: ConfigBundle,
    events: List[BattleEvent],
    tick: int,
) -> Optional[BattleResult]:
    while True:
        attacker = _next_actionable_unit(state, tick)
        if attacker is None:
            return None

        decision = select_target_decision(attacker, state.units)
        target = decision.target
        if target is None:
            return _build_victory_result(state, tick)

        skill_result = try_use_on_attack_skill(
            attacker,
            target,
            state,
            config,
            tick,
            events,
            decision,
        )
        damaged_targets = skill_result.damaged_targets
        if not skill_result.used:
            damaged_targets = [
                _apply_basic_attack(
                    state,
                    events,
                    tick,
                    attacker,
                    target,
                    decision,
                )
            ]

        _trigger_reactions(state, config, events, tick, attacker, damaged_targets)

        if attacker.alive:
            attacker.next_action_tick = tick + attacker.action_interval_ticks
        result = _build_victory_result(state, tick)
        if result:
            return result


def _apply_basic_attack(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    attacker: UnitState,
    target: UnitState,
    decision: Optional[TargetDecision] = None,
) -> UnitState:
    payload = {
        "attacker": attacker.instance_id,
        "target": target.instance_id,
        "target_reason": "current_target",
    }
    if decision is not None:
        payload["target_reason"] = decision.reason
        if decision.score is not None:
            payload["target_score"] = {
                "final": decision.score.final_score,
                "exposure": decision.score.exposure_score,
                "column": decision.score.column_score,
                "low_hp": decision.score.low_hp_score,
                "threat": decision.score.threat_score,
                "role": decision.score.role_score,
                "tie_break": decision.score.tie_break,
            }
    events.append(
        BattleEvent(
            tick=tick,
            event_id=_next_event_id(state),
            type="attack",
            payload=payload,
        )
    )

    amount = calculate_basic_damage(attacker, target)
    reason = "basic_attack"
    died = apply_damage(target, amount, reason=reason, source=attacker.instance_id)
    events.append(
        BattleEvent(
            tick=tick,
            event_id=_next_event_id(state),
            type="damage",
            payload={
                "source": attacker.instance_id,
                "target": target.instance_id,
                "amount": amount,
                "target_hp_after": target.hp,
                "reason": reason,
            },
        )
    )
    if died:
        events.append(
            BattleEvent(
                tick=tick,
                event_id=_next_event_id(state),
                type="death",
                payload={"unit": target.instance_id},
            )
        )
    return target


def _trigger_reactions(
    state: BattleState,
    config: ConfigBundle,
    events: List[BattleEvent],
    tick: int,
    attacker: UnitState,
    damaged_targets: List[UnitState],
) -> None:
    for defender in damaged_targets:
        if not attacker.alive or not defender.alive:
            continue
        try_use_on_attacked_skills(attacker, defender, state, config, tick, events)
        if attacker.alive:
            try_use_on_ally_attacked_skills(attacker, defender, state, config, tick, events)


def _battle_start_event(state: BattleState) -> BattleEvent:
    return BattleEvent(
        tick=0,
        event_id=_next_event_id(state),
        type="battle_start",
        payload={
            "battle_id": state.battle_id,
            "seed": state.seed,
            "tick_rate": state.tick_rate,
            "max_ticks": state.max_ticks,
            "mode": "basic",
        },
    )


def _initialize_action_schedule(state: BattleState) -> None:
    for unit in state.units:
        interval = attack_interval_to_ticks(unit.base_attack_interval, state.tick_rate)
        unit.action_interval_ticks = interval
        unit.next_action_tick = interval


def _next_actionable_unit(state: BattleState, tick: int) -> Optional[UnitState]:
    actionable = [
        unit
        for unit in state.units
        if unit.alive and unit.next_action_tick <= tick
    ]
    if not actionable:
        return None

    actionable.sort(key=lambda unit: (unit.next_action_tick, unit.instance_id))
    return actionable[0]


def _build_victory_result(state: BattleState, tick: int) -> Optional[BattleResult]:
    ally_alive = any(unit.alive and unit.side == "ally" for unit in state.units)
    enemy_alive = any(unit.alive and unit.side == "enemy" for unit in state.units)

    if ally_alive and enemy_alive:
        return None
    if ally_alive:
        return BattleResult(winner="ally", reason="enemy_eliminated", end_tick=tick)
    if enemy_alive:
        return BattleResult(winner="enemy", reason="ally_eliminated", end_tick=tick)
    return BattleResult(winner="draw", reason="mutual_elimination", end_tick=tick)


def _finish_battle(
    state: BattleState,
    events: List[BattleEvent],
    result: BattleResult,
) -> None:
    state.current_tick = result.end_tick
    state.finished = True
    state.result = result
    events.append(
        BattleEvent(
            tick=result.end_tick,
            event_id=_next_event_id(state),
            type="battle_end",
            payload=battle_result_to_dict(result),
        )
    )


def _format_event_id(sequence_number: int) -> str:
    return f"evt_{sequence_number:06d}"


def _next_event_id(state: BattleState) -> str:
    event_id = _format_event_id(state._next_event_number)
    state._next_event_number += 1
    return event_id
