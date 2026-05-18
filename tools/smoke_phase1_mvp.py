#!/usr/bin/env python3
"""Smoke-check generated Phase 1 MVP replay/report artifacts."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple


REQUIRED_EVENT_TYPES = [
    "battle_start",
    "unit_spawn",
    "skill_trigger",
    "attack",
    "damage",
    "death",
    "battle_end",
    "stat_modifier",
    "status_apply",
    "skill_cooldown",
    "action_scheduled",
    "unit_move",
    "target_acquired",
    "enter_range",
    "engage_start",
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
    event_counts, modifier_source_types = (
        _check_replay(replay, args.battle, args.seed, errors) if replay else ({}, set())
    )
    if report:
        _check_report(report, args.battle, args.seed, event_counts, modifier_source_types, errors)
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
    print(f"- modifier source types: {sorted(modifier_source_types)}")
    print(
        "- report: "
        f"total_damage={summary.get('total_damage')}, "
        f"total_kills={summary.get('total_kills')}, "
        f"total_skill_triggers={summary.get('total_skill_triggers')}, "
        f"total_status_applied={summary.get('total_status_applied')}, "
        f"total_skill_cooldowns={summary.get('total_skill_cooldowns')}, "
        f"total_actions_scheduled={summary.get('total_actions_scheduled')}"
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
) -> Tuple[Dict[str, int], Set[str]]:
    _expect(replay.get("schema_version") == "battle_replay.v0.1", "replay schema", errors)
    metadata = _as_dict(replay.get("metadata"))
    _expect(metadata.get("battle_id") == battle_id, "replay battle_id", errors)
    _expect(metadata.get("seed") == seed, "replay seed", errors)
    _expect(isinstance(metadata.get("max_ticks"), int), "replay max_ticks", errors)

    ticks = replay.get("ticks")
    if not isinstance(ticks, list) or not ticks:
        errors.append("replay ticks")
        return {}, set()

    events = []  # type: List[Dict[str, Any]]
    for tick_group in ticks:
        group_events = _as_dict(tick_group).get("events")
        if isinstance(group_events, list):
            events.extend(event for event in group_events if isinstance(event, dict))
    modifier_source_types: Set[str] = {
        event["payload"]["source_type"]
        for event in events
        if event.get("type") == "stat_modifier"
        and isinstance(event.get("payload"), dict)
        and isinstance(event["payload"].get("source_type"), str)
    }
    counts = _event_counts(events)
    attack_with_reason = _filter_events_with_reason(events, "attack")
    skill_trigger_with_reason = _filter_events_with_reason(events, "skill_trigger")
    battle_end_events = [event for event in events if event.get("type") == "battle_end"]

    for event_type in REQUIRED_EVENT_TYPES:
        _expect(counts.get(event_type, 0) > 0, f"replay {event_type} events", errors)
    _expect(len(attack_with_reason) > 0, "replay attack target_reason", errors)
    _expect(len(skill_trigger_with_reason) > 0, "replay skill_trigger target_reason", errors)
    if battle_end_events:
        battle_end = _as_dict(battle_end_events[-1].get("payload"))
        for field in ["winner", "reason", "end_tick", "winner_alive", "loser_alive"]:
            _expect(field in battle_end, f"replay battle_end.{field}", errors)
    else:
        errors.append("expected replay battle_end payload")
    unit_count = metadata.get("unit_count")
    if isinstance(unit_count, int):
        _expect(counts.get("unit_spawn") == unit_count, "replay unit_count", errors)

    result = _as_dict(metadata.get("result"))
    _expect(result.get("winner") in {"ally", "enemy", "draw"}, "replay winner", errors)
    _expect(isinstance(result.get("end_tick"), int), "replay end_tick", errors)
    return counts, modifier_source_types


def _check_report(
    report: Dict[str, Any],
    battle_id: str,
    seed: int,
    event_counts: Dict[str, int],
    modifier_source_types: Set[str],
    errors: List[str],
) -> None:
    _expect(report.get("schema_version") == "battle_report.v0.1", "report schema", errors)
    _expect(report.get("battle_id") == battle_id, "report battle_id", errors)
    _expect(report.get("seed") == seed, "report seed", errors)
    _expect(report.get("winner") in {"ally", "enemy", "draw"}, "report winner", errors)

    summary = _as_dict(report.get("summary"))
    for field in [
        "total_damage",
        "total_kills",
        "total_skill_triggers",
        "total_modifiers",
        "total_status_applied",
        "total_skill_cooldowns",
        "total_actions_scheduled",
    ]:
        _expect(_positive(summary.get(field)), f"report summary.{field}", errors)
    _expect(_non_negative(summary.get("total_status_expired")), "report summary.total_status_expired", errors)
    _expect(summary.get("formation_modifiers", 0) > 0, "report summary.formation_modifiers", errors)
    _expect(summary.get("synergy_modifiers", 0) > 0, "report summary.synergy_modifiers", errors)
    target_reasons = _as_dict(summary.get("target_reason_counts"))
    skill_target_reasons = _as_dict(summary.get("skill_target_reason_counts"))
    _expect(_non_empty_dict(target_reasons), "report target_reason_counts", errors)
    _expect(_non_empty_dict(skill_target_reasons), "report skill_target_reason_counts", errors)
    _expect(summary.get("total_modifiers") == event_counts.get("stat_modifier"), "report modifier count", errors)
    _expect("formation" in modifier_source_types, "replay has formation modifier source", errors)
    _expect("synergy" in modifier_source_types, "replay has synergy modifier source", errors)
    if event_counts:
        _expect(summary.get("total_skill_triggers") == event_counts.get("skill_trigger"), "report trigger count", errors)
        _expect(summary.get("total_kills") == event_counts.get("death"), "report kill count", errors)
        _expect(summary.get("total_status_applied") == event_counts.get("status_apply"), "report status count", errors)
        _expect(summary.get("total_skill_cooldowns") == event_counts.get("skill_cooldown"), "report cooldown count", errors)
        _expect(summary.get("total_actions_scheduled") == event_counts.get("action_scheduled"), "report action schedule count", errors)

    _expect(isinstance(report.get("units"), dict) and len(report.get("units", {})) >= 2, "report units", errors)
    _expect(isinstance(report.get("victory_explanation"), dict), "report victory_explanation", errors)
    top_units = _as_dict(report.get("top_units"))
    for field in ["damage_done", "damage_taken", "skill_triggers"]:
        _expect(isinstance(top_units.get(field), list) and len(top_units.get(field, [])) > 0, f"top_units.{field}", errors)
    _expect(isinstance(report.get("key_moments"), list) and len(report.get("key_moments", [])) > 0, "report key_moments", errors)


def _filter_events_with_reason(events: Sequence[Dict[str, Any]], event_type: str) -> List[Dict[str, Any]]:
    return [
        event
        for event in events
        if event.get("type") == event_type
        and isinstance(event.get("payload"), dict)
        and isinstance(event["payload"].get("target_reason"), str)
        and event["payload"]["target_reason"]
    ]


def _non_empty_dict(value: Dict[str, Any]) -> bool:
    return any(value.values()) if value else False


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


def _non_negative(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0


def _as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _format_counts(counts: Dict[str, int]) -> str:
    return ", ".join(f"{event_type}={counts.get(event_type, 0)}" for event_type in REQUIRED_EVENT_TYPES)


if __name__ == "__main__":
    raise SystemExit(main())
