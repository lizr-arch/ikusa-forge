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
from ikusa_sim.basic_combat import run_basic_combat
from ikusa_sim.combat_rules import (
    apply_damage,
    attack_interval_to_ticks,
    calculate_basic_damage,
    calculate_skill_damage,
)
from ikusa_sim.events import BattleEvent, event_to_dict, events_to_tick_groups
from ikusa_sim.report import build_battle_report, build_battle_report_from_events
from ikusa_sim.rng import BattleRng
from ikusa_sim.runtime_models import BattleResult, BattleState, UnitState
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
    "BattleState",
    "UnitState",
    "apply_damage",
    "attack_interval_to_ticks",
    "battle_result_to_dict",
    "battle_state_to_dict",
    "build_replay_document",
    "build_battle_report",
    "build_battle_report_from_events",
    "calculate_basic_damage",
    "calculate_skill_damage",
    "create_battle_state",
    "event_to_dict",
    "events_to_tick_groups",
    "get_ready_skills",
    "mark_skill_used",
    "run_basic_combat",
    "run_battle_skeleton",
    "select_target",
    "spawn_units_from_encounter",
    "SkillUseResult",
    "try_use_on_ally_attacked_skills",
    "try_use_on_attack_skill",
    "try_use_on_attacked_skills",
    "try_use_on_battle_start_skills",
    "unit_state_to_dict",
]
