"""Runtime battle models for Ikusa Forge Phase 1."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class UnitState:
    instance_id: str
    side: str
    unit_def_id: str
    x: int
    y: int
    role: str
    name: str
    tags: List[str]
    base_hp: int
    base_atk: int
    base_defense: int
    base_range: int
    base_attack_interval: float
    weapon_slots: List[str]
    skill_ids: List[str]
    hp: int
    alive: bool
    next_action_tick: int = 0
    action_interval_ticks: int = 0


@dataclass(frozen=True)
class BattleResult:
    winner: str
    reason: str
    end_tick: int


@dataclass
class BattleState:
    battle_id: str
    seed: int
    tick_rate: int
    max_ticks: int
    current_tick: int
    units: List[UnitState]
    finished: bool
    result: Optional[BattleResult]
    _next_event_number: int
