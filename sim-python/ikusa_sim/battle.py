"""battle.py is a compatibility facade / 兼容转发层.

New code should prefer importing from runtime_models, events, rng, and
battle_skeleton.
"""

from ikusa_sim.battle_skeleton import (
    battle_result_to_dict,
    battle_state_to_dict,
    build_replay_document,
    create_battle_state,
    run_battle_skeleton,
    spawn_units_from_encounter,
    unit_state_to_dict,
)
from ikusa_sim.events import BattleEvent, event_to_dict, events_to_tick_groups
from ikusa_sim.rng import BattleRng
from ikusa_sim.runtime_models import BattleResult, BattleState, UnitState


__all__ = [
    "BattleEvent",
    "BattleResult",
    "BattleRng",
    "BattleState",
    "UnitState",
    "battle_result_to_dict",
    "battle_state_to_dict",
    "build_replay_document",
    "create_battle_state",
    "event_to_dict",
    "events_to_tick_groups",
    "run_battle_skeleton",
    "spawn_units_from_encounter",
    "unit_state_to_dict",
]
