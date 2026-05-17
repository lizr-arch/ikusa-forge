"""Ikusa Forge Python simulator package.

Current implemented scope covers pure config loading, deterministic battle
skeleton output, basic combat rules, minimal skill triggers, and replay reports.
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
from ikusa_sim.battle_session import (
    BattleSession,
    build_battle_snapshot,
    create_battle_session,
    get_events_since,
    initialize_battle_session,
    step_battle_session,
    step_until_finished,
)
from ikusa_sim.combat_rules import (
    apply_damage,
    attack_interval_to_ticks,
    calculate_basic_damage,
    calculate_skill_damage,
)
from ikusa_sim.config_loader import ConfigLoadError, load_config
from ikusa_sim.events import BattleEvent, event_to_dict, events_to_tick_groups
from ikusa_sim.formation import FormationLookupError, build_role_lookup, get_slot_role
from ikusa_sim.live_api import BattleSessionManager, LiveApiError, create_live_api_server
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
from ikusa_sim.report import build_battle_report, build_battle_report_from_events
from ikusa_sim.rng import BattleRng
from ikusa_sim.runtime_models import BattleResult, BattleState, StatusEffect, UnitState
from ikusa_sim.skills import (
    SkillUseResult,
    get_ready_skills,
    mark_skill_used,
    try_use_on_ally_attacked_skills,
    try_use_on_attack_skill,
    try_use_on_attacked_skills,
    try_use_on_battle_start_skills,
)
from ikusa_sim.targeting import select_target

__all__ = [
    "BattleEvent",
    "BattleResult",
    "BattleRng",
    "BattleSession",
    "BattleSessionManager",
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
    "LiveApiError",
    "SkillDef",
    "SynergyDef",
    "StatusEffect",
    "UnitState",
    "UnitDef",
    "WeaponDef",
    "apply_damage",
    "attack_interval_to_ticks",
    "battle_result_to_dict",
    "battle_state_to_dict",
    "build_role_lookup",
    "build_replay_document",
    "build_battle_report",
    "build_battle_report_from_events",
    "build_battle_snapshot",
    "calculate_basic_damage",
    "calculate_skill_damage",
    "create_battle_state",
    "create_battle_session",
    "create_live_api_server",
    "event_to_dict",
    "events_to_tick_groups",
    "get_ready_skills",
    "get_events_since",
    "get_slot_role",
    "initialize_battle_session",
    "load_config",
    "mark_skill_used",
    "run_basic_combat",
    "run_battle_skeleton",
    "select_target",
    "spawn_units_from_encounter",
    "step_battle_session",
    "step_until_finished",
    "SkillUseResult",
    "try_use_on_ally_attacked_skills",
    "try_use_on_attack_skill",
    "try_use_on_attacked_skills",
    "try_use_on_battle_start_skills",
    "unit_state_to_dict",
]
