#!/usr/bin/env python3
"""Run deterministic Ikusa Forge demo battles."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = REPO_ROOT / "sim-python"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from ikusa_sim.battle_skeleton import build_replay_document, run_battle_skeleton  # noqa: E402
from ikusa_sim.basic_combat import run_basic_combat  # noqa: E402
from ikusa_sim.config_loader import ConfigLoadError, load_config  # noqa: E402
from ikusa_sim.events import event_to_dict  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a deterministic Ikusa Forge demo battle.")
    parser.add_argument("--battle", required=True, help="Encounter id to run as the battle id, e.g. demo_001")
    parser.add_argument("--seed", required=True, type=int, help="Deterministic battle seed")
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Generated JSON config directory, e.g. config/generated",
    )
    parser.add_argument("--out", required=True, type=Path, help="Output directory for replay/debug files")
    parser.add_argument(
        "--mode",
        choices=["skeleton", "basic"],
        default="basic",
        help="Battle runner mode. Use skeleton for structural replay only, basic for basic combat rules.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        runner = run_battle_skeleton if args.mode == "skeleton" else run_basic_combat
        state, events = runner(config, args.battle, args.seed)
    except (ConfigLoadError, KeyError, ValueError) as exc:
        print(f"Battle run failed: {exc}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    replay_path = args.out / "replay.json"
    timeline_path = args.out / "debug_timeline.json"
    summary_path = args.out / "run_summary.md"

    _write_json(replay_path, build_replay_document(state, events))
    _write_json(timeline_path, [event_to_dict(event) for event in events])
    with summary_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(_build_run_summary(state, events, args.mode))

    result = state.result
    result_text = f"{result.winner} / {result.reason}" if result else "none"
    print(f"Battle {args.mode} run complete: {args.battle}")
    print(f"- seed: {args.seed}")
    print(f"- units: {len(state.units)}")
    print(f"- events: {len(events)}")
    print(f"- result: {result_text}")
    print(f"- replay: {replay_path}")
    print(f"- debug_timeline: {timeline_path}")
    print(f"- run_summary: {summary_path}")
    return 0


def _write_json(path: Path, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _build_run_summary(state, events, mode) -> str:
    event_counts = {}  # type: Dict[str, int]
    for event in events:
        event_counts[event.type] = event_counts.get(event.type, 0) + 1

    result = state.result
    result_line = "none"
    if result:
        result_line = f"{result.winner} / {result.reason} at tick {result.end_tick}"

    return "\n".join(
        [
            "# Demo Battle Run",
            "",
            f"- mode: `{mode}`",
            f"- battle_id: `{state.battle_id}`",
            f"- seed: `{state.seed}`",
            f"- unit_count: `{len(state.units)}`",
            f"- result: `{result_line}`",
            f"- battle_start events: `{event_counts.get('battle_start', 0)}`",
            f"- unit_spawn events: `{event_counts.get('unit_spawn', 0)}`",
            f"- skill_trigger events: `{event_counts.get('skill_trigger', 0)}`",
            f"- attack events: `{event_counts.get('attack', 0)}`",
            f"- damage events: `{event_counts.get('damage', 0)}`",
            f"- death events: `{event_counts.get('death', 0)}`",
            f"- battle_end events: `{event_counts.get('battle_end', 0)}`",
            "",
            _mode_note(mode),
            "",
        ]
    )


def _mode_note(mode) -> str:
    if mode == "skeleton":
        return "No combat rules applied: no attack, damage, death, targeting AI, skill resolver, synergy application, or formation bonus application runs in skeleton mode."
    return "Basic combat rules applied: targeting AI, basic attack, minimal skill triggers, damage, death, and victory check. Synergies, formation bonuses, battle report, viewer, C# host, and Godot are not implemented."


if __name__ == "__main__":
    raise SystemExit(main())
