"""Ikusa Forge Python simulator package.

Current implemented scope covers pure config loading, deterministic battle
skeleton output, and basic combat rules.
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
from ikusa_sim.basic_combat import run_basic_combat
from ikusa_sim.combat_rules import (
    apply_damage,
    attack_interval_to_ticks,
    calculate_basic_damage,
)
from ikusa_sim.config_loader import ConfigLoadError, load_config
from ikusa_sim.events import BattleEvent, event_to_dict, events_to_tick_groups
from ikusa_sim.formation import FormationLookupError, build_role_lookup, get_slot_role
from ikusa_sim.models import (
    ConfigBundle,
    Constants,
    EncounterDef,
    EncounterUnit,
    FormationDef,
    FormationPattern,
    FormationSlot,
    SkillDef,
    SynergyDef,
    UnitDef,
    WeaponDef,
)
from ikusa_sim.rng import BattleRng
from ikusa_sim.runtime_models import BattleResult, BattleState, UnitState
from ikusa_sim.targeting import select_target

__all__ = [
    "BattleEvent",
    "BattleResult",
    "BattleRng",
    "BattleState",
    "ConfigBundle",
    "ConfigLoadError",
    "Constants",
    "EncounterDef",
    "EncounterUnit",
    "FormationDef",
    "FormationLookupError",
    "FormationPattern",
    "FormationSlot",
    "SkillDef",
    "SynergyDef",
    "UnitState",
    "UnitDef",
    "WeaponDef",
    "apply_damage",
    "attack_interval_to_ticks",
    "battle_result_to_dict",
    "battle_state_to_dict",
    "build_role_lookup",
    "build_replay_document",
    "calculate_basic_damage",
    "create_battle_state",
    "event_to_dict",
    "events_to_tick_groups",
    "get_slot_role",
    "load_config",
    "run_basic_combat",
    "run_battle_skeleton",
    "select_target",
    "spawn_units_from_encounter",
    "unit_state_to_dict",
]
