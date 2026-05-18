"""Step-capable live combat runtime for Ikusa Forge.

This module keeps the current basic combat rules intact while exposing a
BattleSession that can be initialized, stepped, snapshotted, and queried for
new events.
"""

from dataclasses import asdict, dataclass, field
import math
from typing import Any, Dict, List, Optional

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
from ikusa_sim.targeting import TargetCandidateScore, TargetDecision, select_target_decision


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
    _update_spatial_engagements(state, events, tick)
    while True:
        attacker = _next_actionable_unit(state, tick)
        if attacker is None:
            return None

        decision = _select_engaged_target_decision(attacker, state.units)
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
            _emit_action_scheduled(state, events, tick, attacker)
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
    }


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
        if unit.alive and unit.next_action_tick <= tick and _engaged_target_in_attack_range(unit, state.units)
    ]
    if not actionable:
        return None

    actionable.sort(key=lambda unit: (unit.next_action_tick, unit.instance_id))
    return actionable[0]


def _update_spatial_engagements(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
) -> None:
    for unit in sorted((candidate for candidate in state.units if candidate.alive), key=lambda item: item.instance_id):
        target = _nearest_alive_enemy(unit, state.units)
        if target is None:
            unit.engaged_target = None
            unit.velocity_x = 0.0
            unit.velocity_y = 0.0
            unit.movement_intent = "hold"
            continue

        previous_target = unit.engaged_target
        previous_intent = unit.movement_intent
        distance_before = _distance_between(unit, target)
        if previous_target != target.instance_id:
            unit.engaged_target = target.instance_id
            events.append(
                BattleEvent(
                    tick=tick,
                    event_id=_next_event_id(state),
                    type="target_acquired",
                    payload={
                        "unit": unit.instance_id,
                        "target": target.instance_id,
                        "distance": round(distance_before, 3),
                        "reason": "nearest_enemy",
                    },
                )
            )

        if distance_before <= unit.attack_range:
            unit.velocity_x = 0.0
            unit.velocity_y = 0.0
            unit.facing_angle = _angle_to(unit, target)
            unit.movement_intent = "engaged"
            if previous_intent != "engaged" or previous_target != target.instance_id:
                _emit_enter_range_events(state, events, tick, unit, target, distance_before)
            continue

        _move_toward_target(state, events, tick, unit, target)

        distance_after = _distance_between(unit, target)
        if distance_after <= unit.attack_range and (previous_intent != "engaged" or previous_target != target.instance_id):
            unit.movement_intent = "engaged"
            unit.velocity_x = 0.0
            unit.velocity_y = 0.0
            _emit_enter_range_events(state, events, tick, unit, target, distance_after)


def _move_toward_target(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
    target: UnitState,
) -> None:
    distance = _distance_between(unit, target)
    if distance <= 0:
        unit.velocity_x = 0.0
        unit.velocity_y = 0.0
        unit.movement_intent = "engaged"
        return

    step_distance = unit.move_speed / float(max(1, state.tick_rate))
    desired_step = max(0.0, distance - unit.attack_range)
    actual_step = min(step_distance, desired_step)
    direction_x = (target.position_x - unit.position_x) / distance
    direction_y = (target.position_y - unit.position_y) / distance

    old_x = unit.position_x
    old_y = unit.position_y
    unit.position_x += direction_x * actual_step
    unit.position_y += direction_y * actual_step
    unit.velocity_x = direction_x * unit.move_speed if actual_step > 0 else 0.0
    unit.velocity_y = direction_y * unit.move_speed if actual_step > 0 else 0.0
    unit.facing_angle = math.degrees(math.atan2(direction_y, direction_x))
    unit.movement_intent = "move_to_attack_range" if actual_step > 0 else "engaged"

    distance_after = _distance_between(unit, target)
    if actual_step > 0 and (tick % 5 == 0 or distance_after <= unit.attack_range):
        events.append(
            BattleEvent(
                tick=tick,
                event_id=_next_event_id(state),
                type="unit_move",
                payload={
                    "unit": unit.instance_id,
                    "target": target.instance_id,
                    "from_x": round(old_x, 3),
                    "from_y": round(old_y, 3),
                    "to_x": round(unit.position_x, 3),
                    "to_y": round(unit.position_y, 3),
                    "velocity_x": round(unit.velocity_x, 3),
                    "velocity_y": round(unit.velocity_y, 3),
                    "move_speed": unit.move_speed,
                    "distance_to_target": round(distance_after, 3),
                    "reason": "move_to_attack_range",
                },
            )
        )


def _emit_enter_range_events(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
    target: UnitState,
    distance: float,
) -> None:
    payload = {
        "unit": unit.instance_id,
        "target": target.instance_id,
        "distance": round(distance, 3),
        "attack_range": unit.attack_range,
        "engagement_range": unit.engagement_range,
    }
    events.append(
        BattleEvent(
            tick=tick,
            event_id=_next_event_id(state),
            type="enter_range",
            payload=payload,
        )
    )
    events.append(
        BattleEvent(
            tick=tick,
            event_id=_next_event_id(state),
            type="engage_start",
            payload={**payload, "reason": "attack_range_reached"},
        )
    )


def _select_engaged_target_decision(attacker: UnitState, units: List[UnitState]) -> TargetDecision:
    target = _unit_by_id(units, attacker.engaged_target)
    if target is not None and target.alive and target.side != attacker.side and _in_attack_range(attacker, target):
        distance = _distance_between(attacker, target)
        score = TargetCandidateScore(
            unit_id=target.instance_id,
            final_score=max(0, int(1000.0 - distance)),
            exposure_score=max(0, int(200.0 - distance)),
            column_score=max(0, 40 - abs(attacker.x - target.x) * 10),
            low_hp_score=int((1.0 - (float(target.hp) / float(max(1, target.base_hp)))) * 120),
            threat_score=target.atk + target.range * 4 + (15 if target.skill_ids else 0),
            role_score=0,
            tie_break=0,
        )
        return TargetDecision(
            target=target,
            reason="spatial_engaged_target",
            score=score,
            candidates=[score],
        )
    return select_target_decision(attacker, units)


def _engaged_target_in_attack_range(unit: UnitState, units: List[UnitState]) -> bool:
    target = _unit_by_id(units, unit.engaged_target)
    return target is not None and target.alive and target.side != unit.side and _in_attack_range(unit, target)


def _nearest_alive_enemy(unit: UnitState, units: List[UnitState]) -> Optional[UnitState]:
    enemies = [candidate for candidate in units if candidate.alive and candidate.side != unit.side]
    if not enemies:
        return None
    enemies.sort(key=lambda candidate: (_distance_between(unit, candidate), candidate.instance_id))
    return enemies[0]


def _unit_by_id(units: List[UnitState], unit_id: Optional[str]) -> Optional[UnitState]:
    if not unit_id:
        return None
    for unit in units:
        if unit.instance_id == unit_id:
            return unit
    return None


def _in_attack_range(unit: UnitState, target: UnitState) -> bool:
    return _distance_between(unit, target) <= unit.attack_range + 0.001


def _distance_between(left: UnitState, right: UnitState) -> float:
    return math.hypot(left.position_x - right.position_x, left.position_y - right.position_y)


def _angle_to(unit: UnitState, target: UnitState) -> float:
    return math.degrees(math.atan2(target.position_y - unit.position_y, target.position_x - unit.position_x))


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


def _emit_action_scheduled(
    state: BattleState,
    events: List[BattleEvent],
    tick: int,
    unit: UnitState,
) -> None:
    events.append(
        BattleEvent(
            tick=tick,
            event_id=_next_event_id(state),
            type="action_scheduled",
            payload={
                "unit": unit.instance_id,
                "current_tick": tick,
                "next_action_tick": unit.next_action_tick,
                "action_interval_ticks": unit.action_interval_ticks,
                "reason": "after_action",
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
