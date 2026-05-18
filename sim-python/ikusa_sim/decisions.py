"""Decision models for the formalized combat architecture."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class IntentDecision:
    unit_id: str
    intent: str
    reason: str
    score: float
    target_id: Optional[str] = None


@dataclass(frozen=True)
class MovementDecision:
    unit_id: str
    intent: str
    target_id: Optional[str]
    destination_x: float
    destination_y: float
    reason: str
    score: float


@dataclass(frozen=True)
class SkillDecision:
    unit_id: str
    skill_id: Optional[str]
    target_ids: List[str] = field(default_factory=list)
    reason: str = ""
    score: float = 0.0
    can_cast: bool = False


@dataclass(frozen=True)
class ActionDecision:
    unit_id: str
    action_type: str
    target_id: Optional[str]
    reason: str
    score: float
