"""Pure config models for Ikusa Forge.

These dataclasses mirror generated runtime JSON config. They do not represent
runtime battle state, cooldown state, HP changes, events, or reports.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Union


@dataclass(frozen=True)
class Constants:
    tick_rate: int
    max_ticks: int
    board_rows: int
    board_cols: int
    default_seed: int


@dataclass(frozen=True)
class UnitDef:
    id: str
    name: str
    tags: List[str]
    hp: int
    atk: int
    defense: int
    range: int
    attack_interval: float
    weapon_slots: List[str]
    skill_ids: List[str]


@dataclass(frozen=True)
class WeaponDef:
    id: str
    name: str
    type: str
    damage_type: str
    range: int
    cooldown: float
    skill_ids: List[str]


@dataclass(frozen=True)
class SkillDef:
    id: str
    name: str
    trigger: str
    target_rule: str
    cooldown: float
    effect_type: str
    effect_value: Union[int, float]
    tags: List[str]


@dataclass(frozen=True)
class FormationSlot:
    x: int
    y: int
    role: str


@dataclass(frozen=True)
class FormationPattern:
    rows: int
    cols: int
    slots: List[FormationSlot]


@dataclass(frozen=True)
class FormationDef:
    id: str
    name: str
    pattern: FormationPattern
    bonus_rule: str


@dataclass(frozen=True)
class SynergyDef:
    id: str
    name: str
    required_tags: List[str]
    thresholds: Dict[str, Dict[str, Any]]
    scope: str


@dataclass(frozen=True)
class EncounterUnit:
    unit_id: str
    x: int
    y: int


@dataclass(frozen=True)
class EncounterDef:
    id: str
    name: str
    player_units: List[EncounterUnit]
    player_formation: str
    enemy_units: List[EncounterUnit]
    enemy_formation: str
    reward_pool: List[str]


@dataclass(frozen=True)
class ConfigBundle:
    constants: Constants
    units: Dict[str, UnitDef]
    weapons: Dict[str, WeaponDef]
    skills: Dict[str, SkillDef]
    formations: Dict[str, FormationDef]
    synergies: Dict[str, SynergyDef]
    encounters: Dict[str, EncounterDef]
