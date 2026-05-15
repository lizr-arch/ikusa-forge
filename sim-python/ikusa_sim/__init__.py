"""Ikusa Forge Python simulator package.

Current implemented scope is the pure config model boundary. Runtime battle
state and the deterministic battle loop are intentionally not implemented yet.
"""

from ikusa_sim.config_loader import ConfigLoadError, load_config
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

__all__ = [
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
    "UnitDef",
    "WeaponDef",
    "build_role_lookup",
    "get_slot_role",
    "load_config",
]
