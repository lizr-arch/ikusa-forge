"""Formation role lookup helpers.

This module only maps validated formation coordinates to roles. It does not
apply formation bonuses or perform battle logic.
"""

from typing import Dict, Tuple

from ikusa_sim.models import FormationDef


class FormationLookupError(ValueError):
    """Raised when a coordinate is not present in a formation pattern."""


def build_role_lookup(formation: FormationDef) -> Dict[Tuple[int, int], str]:
    lookup = {}
    for slot in formation.pattern.slots:
        coord = (slot.x, slot.y)
        if coord in lookup:
            raise FormationLookupError(f"formation '{formation.id}' has duplicate slot at {coord}")
        lookup[coord] = slot.role
    return lookup


def get_slot_role(formation: FormationDef, x: int, y: int) -> str:
    lookup = build_role_lookup(formation)
    coord = (x, y)
    if coord not in lookup:
        raise FormationLookupError(f"formation '{formation.id}' has no slot at {coord}")
    return lookup[coord]
