"""Basic combat runner for Ikusa Forge Phase 1.

This module implements deterministic targeting, basic attack, damage, death,
and victory checks. It intentionally does not implement skills, synergies,
formation bonuses, battle reports, viewers, host integration, or Godot logic.
"""

from typing import Dict, List, Optional, Tuple

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
from ikusa_sim.events import BattleEvent
from ikusa_sim.models import ConfigBundle
from ikusa_sim.rng import BattleRng
from ikusa_sim.runtime_models import BattleResult, BattleState, UnitState
from ikusa_sim.targeting import select_target


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
    _initialize_action_schedule(state)

    for tick in range(0, state.max_ticks + 1):
        state.current_tick = tick
        result = _run_tick(state, events, tick)
        if result:
            _finish_battle(state, events, result)
            return state, events

    timeout = BattleResult(winner="draw", reason="timeout", end_tick=state.max_ticks)
    _finish_battle(state, events, timeout)
    return state, events


def _run_tick(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
) -> Optional[BattleResult]:
    while True:
        attacker = _next_actionable_unit(state, tick)
        if attacker is None:
            return None

        target = select_target(attacker, state.units)
        if target is None:
            return _build_victory_result(state, tick)

        events.append(
            BattleEvent(
                tick=tick,
                event_id=_next_event_id(state),
                type="attack",
                payload={
                    "attacker": attacker.instance_id,
                    "target": target.instance_id,
                },
            )
        )

        amount = calculate_basic_damage(attacker, target)
        died = apply_damage(target, amount)
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

        attacker.next_action_tick = tick + attacker.action_interval_ticks
        result = _build_victory_result(state, tick)
        if result:
            return result


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
    payload = battle_result_to_dict(result)
    events.append(
        BattleEvent(
            tick=result.end_tick,
            event_id=_next_event_id(state),
            type="battle_end",
            payload=_battle_end_payload(payload),
        )
    )


def _battle_end_payload(result_payload: Dict[str, object]) -> Dict[str, object]:
    payload = dict(result_payload)
    payload["result"] = result_payload
    return payload


def _format_event_id(sequence_number: int) -> str:
    return f"evt_{sequence_number:06d}"


def _next_event_id(state: BattleState) -> str:
    event_id = _format_event_id(state._next_event_number)
    state._next_event_number += 1
    return event_id
