#!/usr/bin/env python3
"""Run the deterministic Ikusa Forge demo battle skeleton."""

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
from ikusa_sim.config_loader import ConfigLoadError, load_config  # noqa: E402
from ikusa_sim.events import event_to_dict  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a deterministic Ikusa Forge battle skeleton.")
    parser.add_argument("--battle", required=True, help="Encounter id to run as the battle id, e.g. demo_001")
    parser.add_argument("--seed", required=True, type=int, help="Deterministic battle seed")
    parser.add_argument(
        "--config",
        required=True,
        type=Path,
        help="Generated JSON config directory, e.g. config/generated",
    )
    parser.add_argument("--out", required=True, type=Path, help="Output directory for replay/debug files")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        state, events = run_battle_skeleton(config, args.battle, args.seed)
    except (ConfigLoadError, KeyError, ValueError) as exc:
        print(f"Battle skeleton run failed: {exc}", file=sys.stderr)
        return 1

    args.out.mkdir(parents=True, exist_ok=True)
    replay_path = args.out / "replay.json"
    timeline_path = args.out / "debug_timeline.json"
    summary_path = args.out / "run_summary.md"

    _write_json(replay_path, build_replay_document(state, events))
    _write_json(timeline_path, [event_to_dict(event) for event in events])
    with summary_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(_build_run_summary(state, events))

    result = state.result
    result_text = f"{result.winner} / {result.reason}" if result else "none"
    print(f"Battle skeleton run complete: {args.battle}")
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


def _build_run_summary(state, events) -> str:
    event_counts = {}  # type: Dict[str, int]
    for event in events:
        event_counts[event.type] = event_counts.get(event.type, 0) + 1

    result = state.result
    result_line = "none"
    if result:
        result_line = f"{result.winner} / {result.reason} at tick {result.end_tick}"

    return "\n".join(
        [
            "# Demo Battle Skeleton Run",
            "",
            f"- battle_id: `{state.battle_id}`",
            f"- seed: `{state.seed}`",
            f"- unit_count: `{len(state.units)}`",
            f"- result: `{result_line}`",
            f"- battle_start events: `{event_counts.get('battle_start', 0)}`",
            f"- unit_spawn events: `{event_counts.get('unit_spawn', 0)}`",
            f"- battle_end events: `{event_counts.get('battle_end', 0)}`",
            "",
            "No combat rules applied: no attack, damage, death, targeting AI, skill resolver, synergy application, or formation bonus application runs in this skeleton.",
            "",
        ]
    )


if __name__ == "__main__":
    raise SystemExit(main())
