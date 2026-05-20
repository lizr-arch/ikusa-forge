"""Step-capable live combat runtime for Ikusa Forge.

This module keeps the current basic combat rules intact while exposing a
BattleSession that can be initialized, stepped, snapshotted, and queried for
new events.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from ikusa_sim.battle_skeleton import (
    battle_result_to_dict,
    create_battle_state,
    spawn_units_from_encounter,
)
from ikusa_sim.combat_rules import (
    attack_interval_to_ticks,
)
from ikusa_sim.events import BattleEvent, event_to_dict
from ikusa_sim.formation_bonus import apply_formation_bonuses
from ikusa_sim.models import ConfigBundle
from ikusa_sim.rng import BattleRng
from ikusa_sim.runtime_models import BattleResult, BattleState, UnitState
from ikusa_sim.skills import (
    try_use_on_ally_attacked_skills,
    try_use_on_attack_skill,
    try_use_on_attacked_skills,
    try_use_on_battle_start_skills,
)
from ikusa_sim.synergy import apply_synergies
from ikusa_sim.targeting import TargetDecision
from ikusa_sim.spatial_combat import (
    engaged_target_in_attack_range,
    initialize_spatial_state,
    select_engaged_target_decision,
    update_spatial_engagements,
)
from ikusa_sim.status_system import apply_status_expire_effect, build_status_expire_effects
from ikusa_sim.unit_fsm import get_unit_combat_state


@dataclass
class BattleSession:
    config: ConfigBundle
    state: BattleState
    battle_id: str
    seed: int
    initialized: bool = False
    finished: bool = False
    current_tick: int = 0
    events: List[BattleEvent] = field(default_factory=list)
    event_cursor: int = 0
    max_ticks: int = 0


def create_battle_session(
    config: ConfigBundle,
    battle_id: str,
    seed: int,
) -> BattleSession:
    if battle_id not in config.encounters:
        raise ValueError(f"Unknown encounter battle_id: {battle_id}")

    rng = BattleRng(seed)
    _ = rng

    state = create_battle_state(config, battle_id, seed)
    return BattleSession(
        config=config,
        state=state,
        battle_id=battle_id,
        seed=seed,
        current_tick=state.current_tick,
        max_ticks=state.max_ticks,
    )


def initialize_battle_session(session: BattleSession) -> List[BattleEvent]:
    if session.initialized:
        return []

    start_index = len(session.events)
    initialize_runtime_state(session)
    return session.events[start_index:]


def initialize_runtime_state(session: BattleSession) -> None:
    state = session.state
    state.current_tick = 0
    session.current_tick = 0
    session.events.append(_battle_start_event(state))
    encounter = session.config.encounters[session.battle_id]
    session.events.extend(spawn_units_from_encounter(session.config, encounter, state))
    initialize_spatial_state(state)
    apply_formation_bonuses(state, session.events)
    apply_synergies(state, session.config, session.events)
    try_use_on_battle_start_skills(state, session.config, session.events)
    _initialize_action_schedule(state)
    session.initialized = True
    session.finished = state.finished


def step_battle_session(session: BattleSession, ticks: int = 1) -> List[BattleEvent]:
    start_index = len(session.events)
    if session.finished:
        return []
    if not session.initialized:
        initialize_battle_session(session)
        return session.events[start_index:]
    if ticks <= 0:
        return []

    for _ in range(ticks):
        if session.finished:
            break

        next_tick = session.current_tick + 1
        if next_tick > session.max_ticks:
            finish_session(session, BattleResult(winner="draw", reason="timeout", end_tick=session.max_ticks))
            break

        session.current_tick = next_tick
        session.state.current_tick = next_tick
        result = run_single_tick(session)
        if result:
            finish_session(session, result)
            break
        if next_tick >= session.max_ticks:
            finish_session(session, BattleResult(winner="draw", reason="timeout", end_tick=session.max_ticks))
            break

    return session.events[start_index:]


def step_until_finished(session: BattleSession) -> List[BattleEvent]:
    start_index = len(session.events)
    if not session.initialized:
        initialize_battle_session(session)

    while not session.finished:
        step_battle_session(session, ticks=1)

    return session.events[start_index:]


def run_single_tick(session: BattleSession) -> Optional[BattleResult]:
    return _run_tick(session.state, session.config, session.events, session.current_tick)


def finish_session(session: BattleSession, result: BattleResult) -> None:
    _finish_battle(session.state, session.events, result)
    session.finished = True
    session.current_tick = session.state.current_tick


def build_battle_snapshot(session: BattleSession) -> Dict[str, Any]:
    state = session.state
    return {
        "schema_version": "battle_snapshot.v0.1",
        "battle_id": session.battle_id,
        "seed": session.seed,
        "tick": session.current_tick,
        "finished": session.finished,
        "result": battle_result_to_dict(state.result) if state.result else None,
        "units": [_unit_snapshot(unit) for unit in state.units],
        "event_count": len(session.events),
    }


def get_events_since(session: BattleSession, event_index: int) -> Dict[str, Any]:
    start = max(0, min(event_index, len(session.events)))
    return {
        "events": [event_to_dict(event) for event in session.events[start:]],
        "next_event_index": len(session.events),
    }


def _run_tick(
    state: BattleState,
    config: ConfigBundle,
    events: List[BattleEvent],
    tick: int,
) -> Optional[BattleResult]:
    _apply_expired_statuses(state, events, tick)
    update_spatial_engagements(state, events, tick)
    while True:
        attacker = _next_actionable_unit(state, tick)
        if attacker is None:
            return None

        decision = select_engaged_target_decision(attacker, state.units)
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
            schedule_next_action=True,
            target_decision=decision,
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
        result = _build_victory_result(state, tick)
        if result:
            return result


def _unit_snapshot(unit: UnitState) -> Dict[str, Any]:
    return {
        "instance_id": unit.instance_id,
        "side": unit.side,
        "unit_def_id": unit.unit_def_id,
        "name": unit.name,
        "x": unit.x,
        "y": unit.y,
        "role": unit.role,
        "combat_state": get_unit_combat_state(unit),
        "hp": unit.hp,
        "base_hp": unit.base_hp,
        "atk": unit.atk,
        "base_atk": unit.base_atk,
        "defense": unit.defense,
        "base_defense": unit.base_defense,
        "range": unit.range,
        "base_range": unit.base_range,
        "position_x": unit.position_x,
        "position_y": unit.position_y,
        "velocity_x": unit.velocity_x,
        "velocity_y": unit.velocity_y,
        "facing_angle": unit.facing_angle,
        "radius": unit.radius,
        "move_speed": unit.move_speed,
        "attack_range": unit.attack_range,
        "engagement_range": unit.engagement_range,
        "engaged_target": unit.engaged_target,
        "movement_intent": unit.movement_intent,
        "alive": unit.alive,
        "next_action_tick": unit.next_action_tick,
        "action_interval_ticks": unit.action_interval_ticks,
        "guard_value": unit.guard_value,
        "skill_cooldowns": dict(unit.skill_cooldowns),
        "statuses": [asdict(status) for status in unit.statuses],
        "formation_anchor_x": unit.formation_anchor_x,
        "formation_anchor_y": unit.formation_anchor_y,
        "formation_group_id": unit.formation_group_id,
        "engagement_target": unit.engagement_target,
        "engagement_role": unit.engagement_role,
        "desired_distance": unit.desired_distance,
        "separation_radius": unit.separation_radius,
    }


def _apply_basic_attack(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    attacker: UnitState,
    target: UnitState,
    decision: Optional[TargetDecision] = None,
) -> UnitState:
    from ikusa_sim.action_pipeline import build_basic_attack_action, run_combat_action

    target_reason = "spatial_engaged_target"
    if decision is not None:
        target_reason = decision.reason

    action = build_basic_attack_action(state, attacker, target, tick)

    action.metadata["target_reason"] = target_reason
    if decision is not None and decision.score is not None:
        action.metadata["target_score"] = {
            "final": decision.score.final_score,
            "exposure": decision.score.exposure_score,
            "column": decision.score.column_score,
            "low_hp": decision.score.low_hp_score,
            "threat": decision.score.threat_score,
            "role": decision.score.role_score,
            "tie_break": decision.score.tie_break,
        }

    run_combat_action(state, action, tick, events, schedule_next_action=True)
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
        if unit.alive and unit.next_action_tick <= tick and engaged_target_in_attack_range(unit, state.units)
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
    if state.finished:
        return
    state.current_tick = result.end_tick
    state.finished = True
    state.result = result
    events.append(
        BattleEvent(
            tick=result.end_tick,
            event_id=_next_event_id(state),
            type="battle_end",
            payload=_battle_end_payload(state, result),
        )
    )


def _apply_expired_statuses(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
) -> None:
    for effect in build_status_expire_effects(state, tick):
        apply_status_expire_effect(state, effect)
        events.append(
            BattleEvent(
                tick=tick,
                event_id=_next_event_id(state),
                type="status_expire",
                payload={
                    "status_id": effect.status_id,
                    "target": effect.target,
                    "stat": effect.stat,
                    "amount": effect.amount,
                    "reason": effect.reason,
                },
            )
        )


def _battle_end_payload(state: BattleState, result: BattleResult) -> dict:
    payload = battle_result_to_dict(result)
    side_stats = {
        "ally": _side_survival_stats(state, "ally"),
        "enemy": _side_survival_stats(state, "enemy"),
    }

    winner_side = result.winner if result.winner in side_stats else None
    loser_side = _opposing_side(winner_side) if winner_side else None
    winner_alive = side_stats[winner_side]["alive"] if winner_side else 0
    loser_alive = side_stats[loser_side]["alive"] if loser_side else 0
    winner_total_hp = side_stats[winner_side]["total_hp"] if winner_side else 0
    loser_total_hp = side_stats[loser_side]["total_hp"] if loser_side else 0

    payload.update(
        {
            "winner_alive": winner_alive,
            "loser_alive": loser_alive,
            "winner_total_hp": winner_total_hp,
            "loser_total_hp": loser_total_hp,
            "summary": _victory_summary(
                result,
                winner_alive,
                loser_alive,
                winner_total_hp,
                loser_total_hp,
            ),
        }
    )
    return payload


def _side_survival_stats(state: BattleState, side: str) -> dict:
    alive_units = [unit for unit in state.units if unit.side == side and unit.alive]
    return {
        "alive": len(alive_units),
        "total_hp": sum(max(0, unit.hp) for unit in alive_units),
    }


def _opposing_side(side: Optional[str]) -> Optional[str]:
    if side == "ally":
        return "enemy"
    if side == "enemy":
        return "ally"
    return None


def _victory_summary(
    result: BattleResult,
    winner_alive: int,
    loser_alive: int,
    winner_total_hp: int,
    loser_total_hp: int,
) -> str:
    if result.winner in {"ally", "enemy"}:
        return (
            f"{result.winner} won by {result.reason} at tick {result.end_tick}; "
            f"winner_alive={winner_alive}, loser_alive={loser_alive}, "
            f"winner_total_hp={winner_total_hp}, loser_total_hp={loser_total_hp}"
        )
    return f"Battle ended as {result.winner} by {result.reason} at tick {result.end_tick}"


def _format_event_id(sequence_number: int) -> str:
    return f"evt_{sequence_number:06d}"


def _next_event_id(state: BattleState) -> str:
    event_id = _format_event_id(state._next_event_number)
    state._next_event_number += 1
    return event_id
