#!/usr/bin/env python3
"""Inspect loaded Ikusa Forge config models without running a battle."""

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = REPO_ROOT / "sim-python"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from ikusa_sim.config_loader import ConfigLoadError, load_config  # noqa: E402
from ikusa_sim.formation import get_slot_role  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect generated Ikusa Forge config models.")
    parser.add_argument("--config", required=True, type=Path, help="Generated JSON config directory")
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        bundle = load_config(args.config)
    except ConfigLoadError as exc:
        print(f"Config model inspection failed: {exc}", file=sys.stderr)
        return 1

    print("Loaded config:")
    print(f"- units: {len(bundle.units)}")
    print(f"- weapons: {len(bundle.weapons)}")
    print(f"- skills: {len(bundle.skills)}")
    print(f"- formations: {len(bundle.formations)}")
    print(f"- encounters: {len(bundle.encounters)}")
    print(f"- tick_rate: {bundle.constants.tick_rate}")
    print(f"- max_ticks: {bundle.constants.max_ticks}")
    print(f"- board: {bundle.constants.board_cols}x{bundle.constants.board_rows}")
    print()

    encounter = bundle.encounters["demo_001"]
    print("Encounter demo_001:")
    _print_side_roles("player", encounter.player_formation, encounter.player_units, bundle)
    _print_side_roles("enemy", encounter.enemy_formation, encounter.enemy_units, bundle)
    return 0


def _print_side_roles(side, formation_id, units, bundle):
    formation = bundle.formations[formation_id]
    print(f"- {side} formation: {formation_id}")
    for unit in units:
        role = get_slot_role(formation, unit.x, unit.y)
        print(f"  {unit.unit_id} at ({unit.x}, {unit.y}) role={role}")


if __name__ == "__main__":
    raise SystemExit(main())
