#!/usr/bin/env python3
"""CSV-first config exporter for Ikusa Forge Phase 1.

v0.1/v0.1.1 reads CSV sample data from config/source/sample_data.
Runtime output is JSON under config/generated.
The command name is kept stable for the planned xlsx adapter.
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


TABLE_ORDER = [
    "units",
    "weapons",
    "skills",
    "formations",
    "synergies",
    "encounters",
    "constants",
]

LIST_FIELDS = {
    "units": {"tags", "weapon_slots", "skill_ids"},
    "weapons": {"skill_ids"},
    "skills": {"tags"},
    "synergies": {"required_tags"},
    "encounters": {"reward_pool"},
}

JSON_FIELDS = {
    "formations": {"pattern"},
    "synergies": {"thresholds"},
    "encounters": {"player_units", "enemy_units"},
}

INTEGER_FIELDS = {
    "units": {"hp", "atk", "defense", "range"},
    "weapons": {"range"},
}

NUMBER_FIELDS = {
    "units": {"attack_interval"},
    "weapons": {"cooldown"},
    "skills": {"cooldown", "effect_value"},
}

INT_PATTERN = re.compile(r"^[+-]?\d+$")
FLOAT_PATTERN = re.compile(r"^[+-]?(?:\d+\.\d*|\d*\.\d+)$")


class ConfigExportError(Exception):
    """Raised when source config cannot be exported."""


def select_source_dir(input_dir: Path) -> Path:
    sample_dir = input_dir / "sample_data"
    if sample_dir.is_dir():
        return sample_dir
    return input_dir


def parse_list_cell(value):
    # type: (str) -> List[str]
    if not value.strip():
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_integer_cell(value: str, *, table: str, field: str, row_number: int) -> int:
    text = value.strip()
    if not INT_PATTERN.match(text):
        raise ConfigExportError(
            f"{table}.csv row {row_number}: field '{field}' must be an integer, got {value!r}"
        )
    return int(text)


def parse_number_cell(value, table, field, row_number):
    text = value.strip()
    if INT_PATTERN.match(text):
        return int(text)
    if FLOAT_PATTERN.match(text):
        return float(text)
    raise ConfigExportError(
        f"{table}.csv row {row_number}: field '{field}' must be a number, got {value!r}"
    )


def parse_json_cell(value: str, *, table: str, field: str, row_number: int) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise ConfigExportError(
            f"{table}.csv row {row_number}: field '{field}' contains invalid JSON: {exc.msg}"
        ) from exc


def parse_scalar_cell(value: str) -> Any:
    text = value.strip()
    lower = text.lower()
    if lower == "true":
        return True
    if lower == "false":
        return False
    if INT_PATTERN.match(text):
        return int(text)
    if FLOAT_PATTERN.match(text):
        return float(text)
    return text


def convert_cell(table: str, field: str, value: str, row_number: int) -> Any:
    value = value.strip()
    if field in LIST_FIELDS.get(table, set()):
        return parse_list_cell(value)
    if field in JSON_FIELDS.get(table, set()):
        return parse_json_cell(value, table=table, field=field, row_number=row_number)
    if field in INTEGER_FIELDS.get(table, set()):
        return parse_integer_cell(value, table=table, field=field, row_number=row_number)
    if field in NUMBER_FIELDS.get(table, set()):
        return parse_number_cell(value, table=table, field=field, row_number=row_number)
    if table == "constants" and field == "value":
        return parse_scalar_cell(value)
    return value


def read_csv_table(csv_path, table):
    # type: (Path, str) -> List[Dict[str, Any]]
    rows = []  # type: List[Dict[str, Any]]
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ConfigExportError(f"{csv_path}: missing header row")

        for row_number, raw_row in enumerate(reader, start=2):
            if None in raw_row:
                extra = ", ".join(raw_row[None])
                raise ConfigExportError(f"{csv_path} row {row_number}: unexpected extra columns: {extra}")

            converted = {
                field: convert_cell(table, field, raw_row.get(field, ""), row_number)
                for field in reader.fieldnames
            }
            rows.append(converted)

    return rows


def build_constants_runtime(rows):
    # type: (List[Dict[str, Any]]) -> Dict[str, Any]
    constants = {}  # type: Dict[str, Any]
    for index, row in enumerate(rows, start=2):
        key = row.get("key", "")
        if not key:
            raise ConfigExportError(f"constants.csv row {index}: missing key")
        if key in constants:
            raise ConfigExportError(f"constants.csv row {index}: duplicate key '{key}'")
        constants[key] = row.get("value")
    return constants


def export_tables(input_dir, output_dir):
    # type: (Path, Path) -> List[Path]
    source_dir = select_source_dir(input_dir)
    if not source_dir.is_dir():
        raise ConfigExportError(f"input directory does not exist: {source_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    written = []  # type: List[Path]

    for table in TABLE_ORDER:
        csv_path = source_dir / f"{table}.csv"
        if not csv_path.is_file():
            raise ConfigExportError(f"missing source table: {csv_path}")

        rows = read_csv_table(csv_path, table)
        runtime_data = build_constants_runtime(rows) if table == "constants" else rows
        output_path = output_dir / f"{table}.json"
        with output_path.open("w", encoding="utf-8", newline="\n") as handle:
            json.dump(runtime_data, handle, indent=2, ensure_ascii=False)
            handle.write("\n")
        written.append(output_path)

    return written


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export Ikusa Forge config to runtime JSON. "
            "v0.1/v0.1.1 reads CSV sample data from config/source/sample_data; "
            "xlsx adapter is planned."
        )
    )
    parser.add_argument("--input", required=True, type=Path, help="Source config directory, e.g. config/source")
    parser.add_argument("--output", required=True, type=Path, help="Generated JSON directory, e.g. config/generated")
    return parser


def main(argv=None):
    # type: (Optional[List[str]]) -> int
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        written = export_tables(args.input, args.output)
    except ConfigExportError as exc:
        print(f"Config export failed: {exc}", file=sys.stderr)
        return 1

    print(f"Exported {len(written)} config tables from {select_source_dir(args.input)} to {args.output}:")
    for path in written:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
