from dataclasses import dataclass
from typing import Optional, Union


@dataclass(frozen=True)
class DamageEffect:
    source: str
    target: str
    amount: int
    reason: str


@dataclass(frozen=True)
class StatusApplyEffect:
    source: str
    target: str
    status_id: str
    stat: str
    amount: int
    expire_tick: Optional[int]
    reason: str


@dataclass(frozen=True)
class CooldownEffect:
    source: str
    skill_id: str
    start_tick: int
    ready_tick: int
    cooldown_ticks: int


@dataclass(frozen=True)
class DeathEffect:
    unit: str
    reason: str


@dataclass(frozen=True)
class ActionScheduleEffect:
    unit: str
    current_tick: int
    next_action_tick: int
    action_interval_ticks: int
    reason: str


Effect = Union[DamageEffect, StatusApplyEffect, CooldownEffect, DeathEffect, ActionScheduleEffect]
