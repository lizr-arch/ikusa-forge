"""Deterministic battle skeleton for Ikusa Forge Phase 1.

This module creates runtime battle state from loaded config and emits a minimal
event stream. It intentionally does not apply attack, damage, death, targeting,
skills, synergies, or formation bonuses.
"""

from dataclasses import asdict
from typing import Any, Dict, List, Sequence, Tuple

from ikusa_sim.events import BattleEvent, events_to_tick_groups
from ikusa_sim.formation import get_slot_role
from ikusa_sim.models import ConfigBundle, EncounterDef, EncounterUnit, UnitDef
from ikusa_sim.rng import BattleRng
from ikusa_sim.runtime_models import BattleResult, BattleState, UnitState


def create_battle_state(config: ConfigBundle, battle_id: str, seed: int) -> BattleState:
    constants = config.constants
    return BattleState(
        battle_id=battle_id,
        seed=seed,
        tick_rate=constants.tick_rate,
        max_ticks=constants.max_ticks,
        current_tick=0,
        units=[],
        finished=False,
        result=None,
        _next_event_number=1,
    )


def spawn_units_from_encounter(
    config: ConfigBundle,
    encounter: EncounterDef,
    state: BattleState,
) -> List[BattleEvent]:
    events = []  # type: List[BattleEvent]
    events.extend(
        _spawn_side_units(
            config,
            state,
            side="ally",
            instance_prefix="ally",
            formation_id=encounter.player_formation,
            encounter_units=encounter.player_units,
        )
    )
    events.extend(
        _spawn_side_units(
            config,
            state,
            side="enemy",
            instance_prefix="enemy",
            formation_id=encounter.enemy_formation,
            encounter_units=encounter.enemy_units,
        )
    )
    return events


def run_battle_skeleton(
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
    events = [
        BattleEvent(
            tick=0,
            event_id=_next_event_id(state),
            type="battle_start",
            payload={
                "battle_id": battle_id,
                "seed": seed,
                "tick_rate": state.tick_rate,
                "max_ticks": state.max_ticks,
            },
        )
    ]

    events.extend(spawn_units_from_encounter(config, encounter, state))

    result = BattleResult(
        winner="draw",
        reason="timeout_no_combat",
        end_tick=state.max_ticks,
    )
    state.current_tick = state.max_ticks
    state.finished = True
    state.result = result
    events.append(
        BattleEvent(
            tick=state.current_tick,
            event_id=_next_event_id(state),
            type="battle_end",
            payload={"result": battle_result_to_dict(result)},
        )
    )

    return state, events


def build_replay_document(state: BattleState, events: Sequence[BattleEvent]) -> Dict[str, Any]:
    return {
        "schema_version": "battle_replay.v0.1",
        "metadata": {
            "battle_id": state.battle_id,
            "seed": state.seed,
            "tick_rate": state.tick_rate,
            "max_ticks": state.max_ticks,
            "unit_count": len(state.units),
            "result": battle_result_to_dict(state.result) if state.result else None,
        },
        "ticks": events_to_tick_groups(events),
    }


def unit_state_to_dict(unit: UnitState) -> Dict[str, Any]:
    return asdict(unit)


def battle_result_to_dict(result: BattleResult) -> Dict[str, Any]:
    return asdict(result)


def battle_state_to_dict(state: BattleState) -> Dict[str, Any]:
    return {
        "battle_id": state.battle_id,
        "seed": state.seed,
        "tick_rate": state.tick_rate,
        "max_ticks": state.max_ticks,
        "current_tick": state.current_tick,
        "units": [unit_state_to_dict(unit) for unit in state.units],
        "finished": state.finished,
        "result": battle_result_to_dict(state.result) if state.result else None,
    }


def _spawn_side_units(
    config: ConfigBundle,
    state: BattleState,
    *,
    side: str,
    instance_prefix: str,
    formation_id: str,
    encounter_units: Sequence[EncounterUnit],
) -> List[BattleEvent]:
    formation = config.formations[formation_id]
    events = []  # type: List[BattleEvent]

    for index, encounter_unit in enumerate(encounter_units, start=1):
        unit_def = config.units[encounter_unit.unit_id]
        unit_state = _create_unit_state(
            unit_def=unit_def,
            encounter_unit=encounter_unit,
            instance_id=f"{instance_prefix}_{index:03d}",
            side=side,
            role=get_slot_role(formation, encounter_unit.x, encounter_unit.y),
        )
        state.units.append(unit_state)
        events.append(
            BattleEvent(
                tick=state.current_tick,
                event_id=_next_event_id(state),
                type="unit_spawn",
                payload={
                    "formation_id": formation_id,
                    "unit": unit_state_to_dict(unit_state),
                },
            )
        )

    return events


def _create_unit_state(
    *,
    unit_def: UnitDef,
    encounter_unit: EncounterUnit,
    instance_id: str,
    side: str,
    role: str,
) -> UnitState:
    return UnitState(
        instance_id=instance_id,
        side=side,
        unit_def_id=unit_def.id,
        x=encounter_unit.x,
        y=encounter_unit.y,
        role=role,
        name=unit_def.name,
        tags=list(unit_def.tags),
        base_hp=unit_def.hp,
        base_atk=unit_def.atk,
        base_defense=unit_def.defense,
        base_range=unit_def.range,
        base_attack_interval=unit_def.attack_interval,
        weapon_slots=list(unit_def.weapon_slots),
        skill_ids=list(unit_def.skill_ids),
        hp=unit_def.hp,
        alive=True,
    )


def _format_event_id(sequence_number: int) -> str:
    return f"evt_{sequence_number:06d}"


def _next_event_id(state: BattleState) -> str:
    event_id = _format_event_id(state._next_event_number)
    state._next_event_number += 1
    return event_id
