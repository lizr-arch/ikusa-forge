#!/usr/bin/env python3
"""Smoke-check curated web viewer demo scenario fixtures."""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


MANIFEST_SCHEMA = "scenario_manifest.v0.1"
REPLAY_SCHEMA = "battle_replay.v0.1"
REPORT_SCHEMA = "battle_report.v0.1"
MIN_SCENARIOS = 3

DEMO_001_REQUIRED_EVENTS = [
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-check curated demo scenario fixtures.")
    parser.add_argument("--samples", required=True, type=Path, help="Samples directory, e.g. web-viewer/public/samples")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    errors = []  # type: List[str]

    manifest_path = args.samples / "manifest.json"
    manifest = load_object(manifest_path, errors)
    scenarios = check_manifest(manifest, errors) if manifest else []

    scenario_summaries = []
    for scenario in scenarios:
        summary = check_scenario(args.samples, scenario, errors)
        if summary:
            scenario_summaries.append(summary)

    if errors:
        print("Demo scenario smoke failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    print("Demo scenario smoke passed")
    print(f"- manifest: {manifest_path}")
    print(f"- scenarios: {len(scenarios)}")
    for summary in scenario_summaries:
        print(
            f"- {summary['id']}: winner={summary['winner']}, reason={summary['reason']}, "
            f"end_tick={summary['end_tick']}, events={summary['events']}"
        )
    return 0


def check_manifest(manifest: Dict[str, Any], errors: List[str]) -> List[Dict[str, Any]]:
    expect(manifest.get("schema_version") == MANIFEST_SCHEMA, "manifest schema_version", errors)
    raw_scenarios = manifest.get("scenarios")
    if not isinstance(raw_scenarios, list):
        errors.append("expected manifest.scenarios list")
        return []
    expect(len(raw_scenarios) >= MIN_SCENARIOS, f"at least {MIN_SCENARIOS} scenarios", errors)

    scenarios = []  # type: List[Dict[str, Any]]
    ids = set()
    for index, raw_scenario in enumerate(raw_scenarios):
        if not isinstance(raw_scenario, dict):
            errors.append(f"scenario[{index}] must be an object")
            continue
        scenario_id = raw_scenario.get("id")
        if not isinstance(scenario_id, str) or not scenario_id:
            errors.append(f"scenario[{index}] missing id")
            continue
        if scenario_id in ids:
            errors.append(f"duplicate scenario id: {scenario_id}")
        ids.add(scenario_id)
        for field in ["name", "description", "replay_url", "report_url"]:
            expect(isinstance(raw_scenario.get(field), str) and raw_scenario.get(field), f"{scenario_id}.{field}", errors)
        expected = raw_scenario.get("expected")
        expect(isinstance(expected, dict), f"{scenario_id}.expected", errors)
        scenarios.append(raw_scenario)
    return scenarios


def check_scenario(samples_dir: Path, scenario: Dict[str, Any], errors: List[str]) -> Optional[Dict[str, Any]]:
    scenario_id = str(scenario.get("id"))
    replay_path = sample_path(samples_dir, scenario.get("replay_url"))
    report_path = sample_path(samples_dir, scenario.get("report_url"))

    replay = load_object(replay_path, errors)
    report = load_object(report_path, errors)
    if not replay or not report:
        return None

    expect(replay.get("schema_version") == REPLAY_SCHEMA, f"{scenario_id} replay schema", errors)
    expect(report.get("schema_version") == REPORT_SCHEMA, f"{scenario_id} report schema", errors)

    result = as_dict(as_dict(replay.get("metadata")).get("result"))
    for field in ["winner", "reason", "end_tick"]:
        expect(field in result and result.get(field) is not None, f"{scenario_id} replay result.{field}", errors)
        expect(field in report and report.get(field) is not None, f"{scenario_id} report.{field}", errors)

    expected = as_dict(scenario.get("expected"))
    if expected:
        expect(report.get("winner") == expected.get("winner"), f"{scenario_id} expected winner", errors)
        expect(report.get("reason") == expected.get("reason"), f"{scenario_id} expected reason", errors)

    events = flatten_events(replay)
    if scenario_id == "demo_001":
        counts = event_counts(events)
        for event_type in DEMO_001_REQUIRED_EVENTS:
            expect(counts.get(event_type, 0) > 0, f"demo_001 {event_type} events", errors)

    return {
        "id": scenario_id,
        "winner": report.get("winner"),
        "reason": report.get("reason"),
        "end_tick": report.get("end_tick"),
        "events": len(events),
    }


def sample_path(samples_dir: Path, url: Any) -> Path:
    if not isinstance(url, str):
        return samples_dir / "__missing__"
    prefix = "/samples/"
    if url.startswith(prefix):
        return samples_dir / url[len(prefix) :]
    return samples_dir / url.lstrip("/")


def load_object(path: Path, errors: List[str]) -> Optional[Dict[str, Any]]:
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


def flatten_events(replay: Dict[str, Any]) -> List[Dict[str, Any]]:
    events = []  # type: List[Dict[str, Any]]
    ticks = replay.get("ticks")
    if not isinstance(ticks, list):
        return events
    for tick_group in ticks:
        group_events = as_dict(tick_group).get("events")
        if isinstance(group_events, list):
            events.extend(event for event in group_events if isinstance(event, dict))
    return events


def event_counts(events: Sequence[Dict[str, Any]]) -> Dict[str, int]:
    counts = {}  # type: Dict[str, int]
    for event in events:
        event_type = event.get("type")
        if isinstance(event_type, str):
            counts[event_type] = counts.get(event_type, 0) + 1
    return counts


def as_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def expect(condition: bool, label: str, errors: List[str]) -> None:
    if not condition:
        errors.append(f"expected {label}")


if __name__ == "__main__":
    raise SystemExit(main())
