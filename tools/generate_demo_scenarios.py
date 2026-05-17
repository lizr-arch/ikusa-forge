#!/usr/bin/env python3
"""Generate curated static demo scenarios for the web viewer."""

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = REPO_ROOT / "sim-python"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from export_xlsx_to_json import ConfigExportError, export_tables, select_source_dir  # noqa: E402
from ikusa_sim.battle_skeleton import build_replay_document  # noqa: E402
from ikusa_sim.basic_combat import run_basic_combat  # noqa: E402
from ikusa_sim.config_loader import ConfigLoadError, load_config  # noqa: E402
from ikusa_sim.events import event_to_dict  # noqa: E402
from ikusa_sim.report import build_battle_report  # noqa: E402
from validate_config import validate_config  # noqa: E402


SCHEMA_VERSION = "scenario_manifest.v0.1"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate curated demo scenario fixtures.")
    parser.add_argument("--source", required=True, type=Path, help="Source config directory, e.g. config/source")
    parser.add_argument(
        "--config-out",
        default=Path("config/generated"),
        type=Path,
        help="Generated runtime config directory, default: config/generated",
    )
    parser.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Static samples directory, e.g. web-viewer/public/samples",
    )
    parser.add_argument("--battle", required=True, help="Encounter id to run, e.g. demo_001")
    parser.add_argument("--seeds", required=True, nargs="+", type=int, help="Scenario seeds to generate")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    if not args.seeds:
        print("Scenario generation failed: at least one seed is required", file=sys.stderr)
        return 1

    try:
        written_config = export_tables(args.source, args.config_out)
        errors = validate_config(args.config_out)
        if errors:
            print("Scenario generation failed: generated config is invalid", file=sys.stderr)
            for error in errors:
                print(f"- {error}", file=sys.stderr)
            return 1

        config = load_config(args.config_out)
        scenarios = [
            generate_scenario(config, args.out, args.battle, seed, index)
            for index, seed in enumerate(args.seeds)
        ]
        write_manifest(args.out, scenarios)
    except (ConfigExportError, ConfigLoadError, KeyError, ValueError, OSError) as exc:
        print(f"Scenario generation failed: {exc}", file=sys.stderr)
        return 1

    print(
        f"Exported {len(written_config)} config tables from "
        f"{select_source_dir(args.source)} to {args.config_out}"
    )
    print(f"Generated {len(scenarios)} demo scenarios for battle {args.battle}:")
    for scenario in scenarios:
        print(
            f"- {scenario['id']}: seed={scenario['seed']}, "
            f"winner={scenario['expected']['winner']}, reason={scenario['expected']['reason']}"
        )
    print(f"- manifest: {args.out / 'manifest.json'}")
    return 0


def generate_scenario(config: Any, output_root: Path, battle_id: str, seed: int, index: int) -> Dict[str, Any]:
    scenario_id = scenario_id_for_seed(battle_id, seed, index)
    scenario_dir = output_root / scenario_id
    scenario_dir.mkdir(parents=True, exist_ok=True)

    state, events = run_basic_combat(config, battle_id, seed)
    replay_doc = build_replay_document(state, events)
    timeline_events = [event_to_dict(event) for event in events]
    report_doc = build_battle_report(replay_doc, timeline_events)

    write_json(scenario_dir / "replay.json", replay_doc)
    write_json(scenario_dir / "battle_report.json", report_doc)

    return {
        "id": scenario_id,
        "battle_id": battle_id,
        "seed": seed,
        "name": scenario_name(scenario_id, seed, index),
        "description": scenario_description(seed, index),
        "replay_url": f"/samples/{scenario_id}/replay.json",
        "report_url": f"/samples/{scenario_id}/battle_report.json",
        "expected": {
            "winner": report_doc.get("winner"),
            "reason": report_doc.get("reason"),
        },
    }


def write_manifest(output_root: Path, scenarios: List[Dict[str, Any]]) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    keep_ids = {scenario["id"] for scenario in scenarios}
    for child in output_root.iterdir():
        if child.name == "manifest.json":
            continue
        if child.is_dir() and child.name not in keep_ids:
            shutil.rmtree(child)

    write_json(
        output_root / "manifest.json",
        {
            "schema_version": SCHEMA_VERSION,
            "scenarios": scenarios,
        },
    )


def write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def scenario_id_for_seed(battle_id: str, seed: int, index: int) -> str:
    return battle_id if index == 0 else f"{battle_id.replace('demo_001', 'demo')}_seed_{seed}"


def scenario_name(scenario_id: str, seed: int, index: int) -> str:
    if index == 0:
        return "Baseline Tactical Demo"
    return f"Baseline Tactical Demo Seed {seed}"


def scenario_description(seed: int, index: int) -> str:
    if index == 0:
        return (
            "Default demo battle with formation, synergy, skills, statuses, cooldowns, "
            "action scheduling, and victory explanation."
        )
    return (
        f"Demo battle scenario slot for seed {seed}. Current combat is deterministic; "
        "this preserves a future randomized scenario slot without changing rules."
    )


if __name__ == "__main__":
    raise SystemExit(main())
