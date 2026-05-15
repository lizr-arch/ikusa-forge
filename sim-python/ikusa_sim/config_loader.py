"""Runtime JSON config loader for Ikusa Forge.

The loader consumes validated JSON from config/generated. It does not read CSV
or xlsx source data and does not create runtime battle state.
"""

import json
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, TypeVar

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


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from validate_config import validate_config  # noqa: E402


T = TypeVar("T")


class ConfigLoadError(Exception):
    """Raised when generated runtime config cannot be loaded safely."""


def load_config(config_dir: Path) -> ConfigBundle:
    """Load validated generated JSON config into pure config dataclasses."""
    config_dir = Path(config_dir)
    errors = validate_config(config_dir)
    if errors:
        joined_errors = "\n".join(f"- {error}" for error in errors)
        raise ConfigLoadError(f"Invalid generated config: {config_dir}\n{joined_errors}")

    return ConfigBundle(
        constants=_build_constants(_load_json_object(config_dir, "constants")),
        units=_index_by_id(_load_json_array(config_dir, "units"), _build_unit),
        weapons=_index_by_id(_load_json_array(config_dir, "weapons"), _build_weapon),
        skills=_index_by_id(_load_json_array(config_dir, "skills"), _build_skill),
        formations=_index_by_id(_load_json_array(config_dir, "formations"), _build_formation),
        synergies=_index_by_id(_load_json_array(config_dir, "synergies"), _build_synergy),
        encounters=_index_by_id(_load_json_array(config_dir, "encounters"), _build_encounter),
    )


def _load_json_array(config_dir: Path, table: str) -> List[Dict[str, Any]]:
    data = _load_json_file(config_dir / f"{table}.json")
    if not isinstance(data, list):
        raise ConfigLoadError(f"{table}.json must contain a JSON array")
    return data


def _load_json_object(config_dir: Path, table: str) -> Dict[str, Any]:
    data = _load_json_file(config_dir / f"{table}.json")
    if not isinstance(data, dict):
        raise ConfigLoadError(f"{table}.json must contain a JSON object")
    return data


def _load_json_file(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ConfigLoadError(f"Could not read generated config file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigLoadError(f"{path}: invalid JSON: {exc.msg}") from exc


def _index_by_id(records: List[Dict[str, Any]], builder: Callable[[Dict[str, Any]], T]) -> Dict[str, T]:
    indexed = {}
    for record in records:
        item = builder(record)
        indexed[record["id"]] = item
    return indexed


def _build_constants(record: Dict[str, Any]) -> Constants:
    return Constants(
        tick_rate=record["tick_rate"],
        max_ticks=record["max_ticks"],
        board_rows=record["board_rows"],
        board_cols=record["board_cols"],
        default_seed=record["default_seed"],
    )


def _build_unit(record: Dict[str, Any]) -> UnitDef:
    return UnitDef(
        id=record["id"],
        name=record["name"],
        tags=list(record["tags"]),
        hp=record["hp"],
        atk=record["atk"],
        defense=record["defense"],
        range=record["range"],
        attack_interval=record["attack_interval"],
        weapon_slots=list(record["weapon_slots"]),
        skill_ids=list(record["skill_ids"]),
    )


def _build_weapon(record: Dict[str, Any]) -> WeaponDef:
    return WeaponDef(
        id=record["id"],
        name=record["name"],
        type=record["type"],
        damage_type=record["damage_type"],
        range=record["range"],
        cooldown=record["cooldown"],
        skill_ids=list(record["skill_ids"]),
    )


def _build_skill(record: Dict[str, Any]) -> SkillDef:
    return SkillDef(
        id=record["id"],
        name=record["name"],
        trigger=record["trigger"],
        target_rule=record["target_rule"],
        cooldown=record["cooldown"],
        effect_type=record["effect_type"],
        effect_value=record["effect_value"],
        tags=list(record["tags"]),
    )


def _build_formation(record: Dict[str, Any]) -> FormationDef:
    pattern = record["pattern"]
    return FormationDef(
        id=record["id"],
        name=record["name"],
        pattern=FormationPattern(
            rows=pattern["rows"],
            cols=pattern["cols"],
            slots=[
                FormationSlot(x=slot["x"], y=slot["y"], role=slot["role"])
                for slot in pattern["slots"]
            ],
        ),
        bonus_rule=record["bonus_rule"],
    )


def _build_synergy(record: Dict[str, Any]) -> SynergyDef:
    return SynergyDef(
        id=record["id"],
        name=record["name"],
        required_tags=list(record["required_tags"]),
        thresholds=dict(record["thresholds"]),
        scope=record["scope"],
    )


def _build_encounter(record: Dict[str, Any]) -> EncounterDef:
    return EncounterDef(
        id=record["id"],
        name=record["name"],
        player_units=[_build_encounter_unit(unit) for unit in record["player_units"]],
        player_formation=record["player_formation"],
        enemy_units=[_build_encounter_unit(unit) for unit in record["enemy_units"]],
        enemy_formation=record["enemy_formation"],
        reward_pool=list(record["reward_pool"]),
    )


def _build_encounter_unit(record: Dict[str, Any]) -> EncounterUnit:
    return EncounterUnit(unit_id=record["unit_id"], x=record["x"], y=record["y"])
