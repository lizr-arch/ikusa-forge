#!/usr/bin/env python3
"""Smoke-check generated Phase 1 MVP replay/report artifacts."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


REQUIRED_EVENT_TYPES = [
    "battle_start",
    "unit_spawn",
    "skill_trigger",
    "attack",
    "damage",
    "death",
    "battle_end",
]

REQUIRED_VIEWER_FILES = [
    "index.html",
    "package.json",
    "src/main.ts",
    "src/replayState.ts",
    "src/boardView.ts",
    "src/timelineView.ts",
    "src/reportView.ts",
    "src/unitDetailView.ts",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-check Ikusa Forge Phase 1 MVP artifacts.")
    parser.add_argument("--run", type=Path, default=Path("runs/demo_001"))
    parser.add_argument("--viewer", type=Path, default=Path("web-viewer"))
    parser.add_argument("--battle", default="demo_001")
    parser.add_argument("--seed", type=int, default=1001)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    errors = []  # type: List[str]

    replay_path = args.run / "replay.json"
    report_path = args.run / "battle_report.json"
    replay = _load_object(replay_path, errors)
    report = _load_object(report_path, errors)
    event_counts = _check_replay(replay, args.battle, args.seed, errors) if replay else {}
    if report:
        _check_report(report, args.battle, args.seed, event_counts, errors)
    _check_viewer(args.viewer, errors)

    if errors:
        print("Phase 1 MVP smoke failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    metadata = _as_dict(replay.get("metadata")) if replay else {}
    result = _as_dict(metadata.get("result"))
    summary = _as_dict(report.get("summary")) if report else {}
    print("Phase 1 MVP smoke passed")
    print(f"- battle_id: {args.battle}")
    print(f"- seed: {args.seed}")
    print(f"- replay: {replay_path}")
    print(f"- battle_report: {report_path}")
    print(f"- viewer: {args.viewer}")
    print(f"- winner: {result.get('winner')} / {result.get('reason')} at tick {result.get('end_tick')}")
    print(f"- events: {_format_counts(event_counts)}")
    print(
        "- report: "
        f"total_damage={summary.get('total_damage')}, "
        f"total_kills={summary.get('total_kills')}, "
        f"total_skill_triggers={summary.get('total_skill_triggers')}"
    )
    return 0


def _load_object(path: Path, errors: List[str]) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        errors.append(f"missing file: {path}")
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{path}: invalid JSON: {exc.msg}")
        return None
    if not isinstance(data, dict):
        errors.append(f"{path}: expected top-level object")
        return None
    return data


def _check_replay(
    replay: Dict[str, Any],
    battle_id: str,
    seed: int,
    errors: List[str],
) -> Dict[str, int]:
    _expect(replay.get("schema_version") == "battle_replay.v0.1", "replay schema", errors)
    metadata = _as_dict(replay.get("metadata"))
    _expect(metadata.get("battle_id") == battle_id, "replay battle_id", errors)
    _expect(metadata.get("seed") == seed, "replay seed", errors)
    _expect(isinstance(metadata.get("max_ticks"), int), "replay max_ticks", errors)

    ticks = replay.get("ticks")
    if not isinstance(ticks, list) or not ticks:
        errors.append("replay ticks")
        return {}

    events = []  # type: List[Dict[str, Any]]
    for tick_group in ticks:
        group_events = _as_dict(tick_group).get("events")
        if isinstance(group_events, list):
            events.extend(event for event in group_events if isinstance(event, dict))
    counts = _event_counts(events)

    for event_type in REQUIRED_EVENT_TYPES:
        _expect(counts.get(event_type, 0) > 0, f"replay {event_type} events", errors)
    unit_count = metadata.get("unit_count")
    if isinstance(unit_count, int):
        _expect(counts.get("unit_spawn") == unit_count, "replay unit_count", errors)

    result = _as_dict(metadata.get("result"))
    _expect(result.get("winner") in {"ally", "enemy", "draw"}, "replay winner", errors)
    _expect(isinstance(result.get("end_tick"), int), "replay end_tick", errors)
    return counts


def _check_report(
    report: Dict[str, Any],
    battle_id: str,
    seed: int,
    event_counts: Dict[str, int],
    errors: List[str],
) -> None:
    _expect(report.get("schema_version") == "battle_report.v0.1", "report schema", errors)
    _expect(report.get("battle_id") == battle_id, "report battle_id", errors)
    _expect(report.get("seed") == seed, "report seed", errors)
    _expect(report.get("winner") in {"ally", "enemy", "draw"}, "report winner", errors)

    summary = _as_dict(report.get("summary"))
    for field in ["total_damage", "total_kills", "total_skill_triggers"]:
        _expect(_positive(summary.get(field)), f"report summary.{field}", errors)
    if event_counts:
        _expect(summary.get("total_skill_triggers") == event_counts.get("skill_trigger"), "report trigger count", errors)
        _expect(summary.get("total_kills") == event_counts.get("death"), "report kill count", errors)

    _expect(isinstance(report.get("units"), dict) and len(report.get("units", {})) >= 2, "report units", errors)
    top_units = _as_dict(report.get("top_units"))
    for field in ["damage_done", "damage_taken", "skill_triggers"]:
        _expect(isinstance(top_units.get(field), list) and len(top_units.get(field, [])) > 0, f"top_units.{field}", errors)
    _expect(isinstance(report.get("key_moments"), list) and len(report.get("key_moments", [])) > 0, "report key_moments", errors)


def _check_viewer(viewer_dir: Path, errors: List[str]) -> None:
    for relative_path in REQUIRED_VIEWER_FILES:
        _expect((viewer_dir / relative_path).is_file(), f"viewer file {relative_path}", errors)


def _event_counts(events: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = {}  # type: Dict[str, int]
    for event in events:
        event_type = event.get("type")
        if isinstance(event_type, str):
            counts[event_type] = counts.get(event_type, 0) + 1
    return counts


def _expect(condition: bool, label: str, errors: List[str]) -> None:
    if not condition:
        errors.append(f"expected {label}")


def _positive(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value > 0


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _format_counts(counts: Dict[str, int]) -> str:
    return ", ".join(f"{event_type}={counts.get(event_type, 0)}" for event_type in REQUIRED_EVENT_TYPES)


if __name__ == "__main__":
    raise SystemExit(main())
