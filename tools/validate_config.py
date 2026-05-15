#!/usr/bin/env python3
"""Validate generated Ikusa Forge runtime config JSON."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


DATA_TABLES = [
    "units",
    "weapons",
    "skills",
    "formations",
    "synergies",
    "encounters",
]

REQUIRED_FIELDS = {
    "units": [
        "id",
        "name",
        "tags",
        "hp",
        "atk",
        "defense",
        "range",
        "attack_interval",
        "weapon_slots",
        "skill_ids",
    ],
    "weapons": ["id", "name", "type", "damage_type", "range", "cooldown", "skill_ids"],
    "skills": ["id", "name", "trigger", "target_rule", "cooldown", "effect_type", "effect_value", "tags"],
    "formations": ["id", "name", "pattern", "bonus_rule"],
    "synergies": ["id", "name", "required_tags", "thresholds", "scope"],
    "encounters": [
        "id",
        "name",
        "player_units",
        "player_formation",
        "enemy_units",
        "enemy_formation",
        "reward_pool",
    ],
}

NONNEGATIVE_FIELDS = {
    "units": ["hp", "atk", "defense", "range", "attack_interval"],
    "weapons": ["range", "cooldown"],
    "skills": ["cooldown"],
}

REQUIRED_CONSTANT_KEYS = {"tick_rate", "max_ticks", "board_rows", "board_cols", "default_seed"}
NONNEGATIVE_CONSTANT_KEYS = {"tick_rate", "max_ticks", "board_rows", "board_cols"}


def load_json_table(input_dir, table, errors):
    # type: (Path, str, List[str]) -> List[Dict[str, Any]]
    path = input_dir / f"{table}.json"
    if not path.is_file():
        errors.append(f"missing generated file: {path}")
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc.msg}")
        return []

    if not isinstance(data, list):
        errors.append(f"{path}: expected top-level array")
        return []

    records = []  # type: List[Dict[str, Any]]
    for index, item in enumerate(data):
        if isinstance(item, dict):
            records.append(item)
        else:
            errors.append(f"{table}[{index}]: expected object")
    return records


def load_constants(input_dir, errors):
    # type: (Path, List[str]) -> Dict[str, Any]
    path = input_dir / "constants.json"
    if not path.is_file():
        errors.append(f"missing generated file: {path}")
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc.msg}")
        return {}

    if not isinstance(data, dict) or isinstance(data, list):
        errors.append(f"{path}: expected top-level object")
        return {}
    return data


def record_label(table, record, index):
    # type: (str, Dict[str, Any], int) -> str
    key = "key" if table == "constants" else "id"
    value = record.get(key)
    if isinstance(value, str) and value:
        return f"{table}.{value}"
    return f"{table}[{index}]"


def validate_required_fields(table, records, errors):
    # type: (str, List[Dict[str, Any]], List[str]) -> None
    for index, record in enumerate(records):
        for field in REQUIRED_FIELDS[table]:
            if field not in record or record[field] == "":
                errors.append(f"{record_label(table, record, index)}: missing required field '{field}'")


def validate_unique_key(table, records, errors):
    # type: (str, List[Dict[str, Any]], List[str]) -> None
    key = "key" if table == "constants" else "id"
    seen = {}  # type: Dict[str, int]
    for index, record in enumerate(records):
        value = record.get(key)
        if not isinstance(value, str) or not value:
            errors.append(f"{table}[{index}]: missing unique field '{key}'")
            continue
        if value in seen:
            errors.append(f"{table}: duplicate {key} '{value}' at rows {seen[value]} and {index}")
        else:
            seen[value] = index


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def is_integer(value):
    # type: (Any) -> bool
    return isinstance(value, int) and not isinstance(value, bool)


def validate_nonnegative_numbers(table, records, errors):
    # type: (str, List[Dict[str, Any]], List[str]) -> None
    for index, record in enumerate(records):
        for field in NONNEGATIVE_FIELDS.get(table, []):
            value = record.get(field)
            if not is_number(value):
                errors.append(f"{record_label(table, record, index)}: field '{field}' must be numeric")
            elif value < 0:
                errors.append(f"{record_label(table, record, index)}: field '{field}' must not be negative")


def collect_ids(records):
    # type: (List[Dict[str, Any]]) -> Set[str]
    return {record["id"] for record in records if isinstance(record.get("id"), str) and record["id"]}


def validate_unit_references(units, skill_ids, weapon_types, errors):
    # type: (List[Dict[str, Any]], Set[str], Set[str], List[str]) -> None
    for index, unit in enumerate(units):
        label = record_label("units", unit, index)
        for skill_id in unit.get("skill_ids", []):
            if skill_id not in skill_ids:
                errors.append(f"{label}: skill_ids references unknown skill '{skill_id}'")
        for weapon_type in unit.get("weapon_slots", []):
            if weapon_type not in weapon_types:
                errors.append(f"{label}: weapon_slots references unknown weapon type '{weapon_type}'")


def validate_weapon_references(weapons, skill_ids, errors):
    # type: (List[Dict[str, Any]], Set[str], List[str]) -> None
    for index, weapon in enumerate(weapons):
        label = record_label("weapons", weapon, index)
        for skill_id in weapon.get("skill_ids", []):
            if skill_id not in skill_ids:
                errors.append(f"{label}: skill_ids references unknown skill '{skill_id}'")


def validate_formation_patterns(formations, errors):
    # type: (List[Dict[str, Any]], List[str]) -> None
    for index, formation in enumerate(formations):
        label = record_label("formations", formation, index)
        pattern = formation.get("pattern")
        if not isinstance(pattern, dict):
            errors.append(f"{label}: pattern must be an object")
            continue

        rows = pattern.get("rows")
        cols = pattern.get("cols")
        if rows != 3 or cols != 4:
            errors.append(f"{label}: pattern must use v0.1 board size rows=3 cols=4")

        slots = pattern.get("slots")
        if not isinstance(slots, list) or not slots:
            errors.append(f"{label}: pattern.slots must be a non-empty list")
            continue

        seen_coords = set()  # type: Set[Tuple[int, int]]
        for slot_index, slot in enumerate(slots):
            if not isinstance(slot, dict):
                errors.append(f"{label}: pattern.slots[{slot_index}] must be an object")
                continue

            x = slot.get("x")
            y = slot.get("y")
            if not isinstance(x, int) or not isinstance(y, int):
                errors.append(f"{label}: pattern.slots[{slot_index}] must contain integer x/y")
                continue
            if x < 0 or x >= 4 or y < 0 or y >= 3:
                errors.append(f"{label}: pattern.slots[{slot_index}] coordinate ({x}, {y}) is outside 4x3 board")
                continue
            coord = (x, y)
            if coord in seen_coords:
                errors.append(f"{label}: duplicate formation coordinate ({x}, {y})")
            seen_coords.add(coord)


def validate_encounter_unit_list(encounter_label, field, entries, unit_ids, errors):
    # type: (str, str, Any, Set[str], List[str]) -> None
    if not isinstance(entries, list) or not entries:
        errors.append(f"{encounter_label}: {field} must be a non-empty list")
        return

    seen_coords = set()  # type: Set[Tuple[int, int]]
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"{encounter_label}: {field}[{index}] must be an object")
            continue

        unit_id = entry.get("unit_id")
        if unit_id not in unit_ids:
            errors.append(f"{encounter_label}: {field}[{index}] references unknown unit '{unit_id}'")

        x = entry.get("x")
        y = entry.get("y")
        if not isinstance(x, int) or not isinstance(y, int):
            errors.append(f"{encounter_label}: {field}[{index}] must contain integer x/y")
            continue
        if x < 0 or x >= 4 or y < 0 or y >= 3:
            errors.append(f"{encounter_label}: {field}[{index}] coordinate ({x}, {y}) is outside 4x3 board")
            continue

        coord = (x, y)
        if coord in seen_coords:
            errors.append(f"{encounter_label}: duplicate {field} coordinate ({x}, {y})")
        seen_coords.add(coord)


def validate_encounters(encounters, unit_ids, formation_ids, errors):
    # type: (List[Dict[str, Any]], Set[str], Set[str], List[str]) -> None
    for index, encounter in enumerate(encounters):
        label = record_label("encounters", encounter, index)

        player_formation = encounter.get("player_formation")
        if player_formation not in formation_ids:
            errors.append(f"{label}: player_formation references unknown formation '{player_formation}'")

        enemy_formation = encounter.get("enemy_formation")
        if enemy_formation not in formation_ids:
            errors.append(f"{label}: enemy_formation references unknown formation '{enemy_formation}'")

        validate_encounter_unit_list(label, "player_units", encounter.get("player_units"), unit_ids, errors)
        validate_encounter_unit_list(label, "enemy_units", encounter.get("enemy_units"), unit_ids, errors)


def validate_constants(constants, errors):
    # type: (Dict[str, Any], List[str]) -> None
    missing = sorted(REQUIRED_CONSTANT_KEYS - set(constants.keys()))
    for key in missing:
        errors.append(f"constants: missing required key '{key}'")

    for key in sorted(REQUIRED_CONSTANT_KEYS & set(constants.keys())):
        value = constants[key]
        if not is_integer(value):
            errors.append(f"constants.{key}: value must be an integer")
            continue
        if key in NONNEGATIVE_CONSTANT_KEYS and value < 0:
            errors.append(f"constants.{key}: value must not be negative")


def validate_config(input_dir):
    # type: (Path) -> List[str]
    errors = []  # type: List[str]
    tables = {table: load_json_table(input_dir, table, errors) for table in DATA_TABLES}
    constants = load_constants(input_dir, errors)

    for table, records in tables.items():
        validate_required_fields(table, records, errors)
        validate_unique_key(table, records, errors)
        validate_nonnegative_numbers(table, records, errors)

    skill_ids = collect_ids(tables["skills"])
    unit_ids = collect_ids(tables["units"])
    formation_ids = collect_ids(tables["formations"])
    weapon_types = {
        record["type"]
        for record in tables["weapons"]
        if isinstance(record.get("type"), str) and record["type"]
    }

    validate_unit_references(tables["units"], skill_ids, weapon_types, errors)
    validate_weapon_references(tables["weapons"], skill_ids, errors)
    validate_formation_patterns(tables["formations"], errors)
    validate_encounters(tables["encounters"], unit_ids, formation_ids, errors)
    validate_constants(constants, errors)

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate generated Ikusa Forge runtime JSON config.")
    parser.add_argument("--input", required=True, type=Path, help="Generated JSON directory, e.g. config/generated")
    return parser


def main(argv=None):
    # type: (Optional[List[str]]) -> int
    parser = build_parser()
    args = parser.parse_args(argv)

    errors = validate_config(args.input)
    if errors:
        print("Config validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"Config validation passed: {args.input}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
