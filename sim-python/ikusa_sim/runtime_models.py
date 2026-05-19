"""Runtime battle models for Ikusa Forge Phase 1."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class StatusEffect:
    id: str
    source: str
    source_type: str
    target: str
    stat: str
    amount: int
    start_tick: int
    expire_tick: Optional[int]
    reason: str


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
    formation_id: str = ""
    next_action_tick: int = 0
    action_interval_ticks: int = 0
    guard_value: int = 0
    position_x: float = 0.0
    position_y: float = 0.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    facing_angle: float = 0.0
    radius: float = 8.0
    move_speed: float = 24.0
    attack_range: float = 18.0
    engagement_range: float = 22.0
    engaged_target: Optional[str] = None
    formation_anchor_x: float = 0.0
    formation_anchor_y: float = 0.0
    formation_group_id: str = ""
    engagement_target: Optional[str] = None
    engagement_role: str = "frontline"
    desired_distance: float = 0.0
    separation_radius: float = 14.4
    movement_intent: str = "hold"
    combat_state: str = "idle"
    statuses: List[StatusEffect] = field(default_factory=list)
    skill_cooldowns: Dict[str, int] = field(default_factory=dict)
    atk: int = field(init=False)
    defense: int = field(init=False)
    range: int = field(init=False)

    def __post_init__(self) -> None:
        self.atk = self.base_atk
        self.defense = self.base_defense
        self.range = self.base_range

        if self.formation_group_id == "":
            self.formation_group_id = self.side

        _text_sources = [
            name.lower() for name in [self.unit_def_id, self.name] if name
        ] + [tag.lower() for tag in self.tags]

        def _any_text_has(*keywords: str) -> bool:
            return any(
                any(kw in text for kw in keywords)
                for text in _text_sources
            )

        role_lower = self.role.lower()

        # Priority: ninja > ranged > support > frontline
        if _any_text_has("ninja"):
            self.engagement_role = "flanker"
        elif _any_text_has("bow", "archer", "yumi", "ranged") or any(
            "bow" in (slot.lower() if slot else "") for slot in (self.weapon_slots or [])
        ):
            self.engagement_role = "ranged"
        elif _any_text_has("banner", "flag", "support"):
            self.engagement_role = "support"
        elif any(kw in role_lower for kw in ("shield", "spear", "katana", "samurai", "vanguard", "front")):
            self.engagement_role = "frontline"
        # else keep default "frontline"

        if self.desired_distance == 0.0:
            eng_role = self.engagement_role
            if eng_role == "ranged":
                self.desired_distance = self.attack_range * 0.65
            elif eng_role == "support":
                self.desired_distance = max(40.0, self.attack_range)
            else:
                self.desired_distance = self.attack_range * 0.85

        if self.separation_radius == 14.4:
            self.separation_radius = self.radius * 1.8


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
