"""battle.py is a compatibility facade / 兼容转发层.

New code should prefer importing from runtime_models, events, rng,
battle_skeleton, targeting, combat_rules, basic_combat, skills, and report.
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
from ikusa_sim.actions import (
    ActionResult,
    CombatAction,
    build_basic_attack_action,
    build_skill_action,
    resolve_combat_action,
    validate_combat_action,
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
from ikusa_sim.decisions import (
    ActionDecision,
    IntentDecision,
    MovementDecision,
    SkillDecision,
)
from ikusa_sim.events import BattleEvent, event_to_dict, events_to_tick_groups
from ikusa_sim.live_api import BattleSessionManager, LiveApiError, create_live_api_server
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
from ikusa_sim.unit_fsm import (
    UnitCombatState,
    can_transition_unit_state,
    get_unit_combat_state,
    set_unit_combat_state,
)


__all__ = [
    "BattleEvent",
    "BattleResult",
    "BattleRng",
    "BattleSession",
    "BattleSessionManager",
    "BattleState",
    "ActionDecision",
    "ActionResult",
    "UnitState",
    "CombatAction",
    "LiveApiError",
    "apply_damage",
    "attack_interval_to_ticks",
    "battle_result_to_dict",
    "battle_state_to_dict",
    "build_replay_document",
    "build_battle_report",
    "build_battle_report_from_events",
    "build_battle_snapshot",
    "calculate_basic_damage",
    "calculate_skill_damage",
    "can_transition_unit_state",
    "create_battle_state",
    "create_battle_session",
    "create_live_api_server",
    "event_to_dict",
    "events_to_tick_groups",
    "get_ready_skills",
    "get_events_since",
    "get_unit_combat_state",
    "initialize_battle_session",
    "mark_skill_used",
    "build_basic_attack_action",
    "build_skill_action",
    "run_basic_combat",
    "run_battle_skeleton",
    "IntentDecision",
    "MovementDecision",
    "select_target",
    "set_unit_combat_state",
    "resolve_combat_action",
    "spawn_units_from_encounter",
    "SkillUseResult",
    "SkillDecision",
    "UnitCombatState",
    "StatusEffect",
    "step_battle_session",
    "step_until_finished",
    "validate_combat_action",
    "try_use_on_ally_attacked_skills",
    "try_use_on_attack_skill",
    "try_use_on_attacked_skills",
    "try_use_on_battle_start_skills",
    "unit_state_to_dict",
]
