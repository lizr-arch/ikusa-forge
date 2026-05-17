#!/usr/bin/env python3
"""Smoke-check a running Ikusa Forge Live Combat API server."""

import argparse
import json
import sys
from typing import Any, Dict, Optional, Sequence
from urllib import error, parse, request


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Smoke-check Ikusa Forge Live Combat API / 实时战斗 API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--battle", default="demo_001")
    parser.add_argument("--seed", type=int, default=1001)
    parser.add_argument("--max-steps", type=int, default=100)
    parser.add_argument("--step-ticks", type=int, default=5)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        summary = run_smoke(args.host, args.port, args.battle, args.seed, args.max_steps, args.step_ticks)
    except SmokeError as exc:
        print("Live API smoke failed:", file=sys.stderr)
        print(f"- {exc}", file=sys.stderr)
        return 1

    print("Live API smoke passed")
    print(f"- service: {summary['service']}")
    print(f"- session_id: {summary['session_id']}")
    print(f"- start_events: {summary['start_events']}")
    print(f"- steps: {summary['steps']}")
    print(f"- final: {summary['winner']} / {summary['reason']} at tick {summary['end_tick']}")
    print(f"- events: {summary['events']}")
    print(f"- next_event_index: {summary['next_event_index']}")
    print("- reset: ok")
    return 0


def run_smoke(
    host: str,
    port: int,
    battle_id: str,
    seed: int,
    max_steps: int,
    step_ticks: int,
) -> Dict[str, Any]:
    base_url = f"http://{host}:{port}"
    health = _request_json("GET", f"{base_url}/api/health")
    _expect(health.get("ok") is True, "health ok")
    _expect(health.get("service") == "ikusa-live-api", "health service")

    start = _request_json(
        "POST",
        f"{base_url}/api/battle/start",
        {"battle_id": battle_id, "seed": seed},
    )
    _expect(start.get("ok") is True, "start ok")
    session_id = _expect_str(start.get("session_id"), "session_id")
    snapshot = _expect_dict(start.get("snapshot"), "start snapshot")
    events = _expect_list(start.get("events"), "start events")
    _expect(snapshot.get("schema_version") == "battle_snapshot.v0.1", "snapshot schema_version")
    _expect(snapshot.get("tick") == 0, "start tick 0")
    _expect(any(event.get("type") == "battle_start" for event in events), "start battle_start event")
    _expect(any(event.get("type") == "unit_spawn" for event in events), "start unit_spawn event")

    current = start
    steps = 0
    while not _expect_dict(current.get("snapshot"), "step snapshot").get("finished"):
        if steps >= max_steps:
            raise SmokeError(f"battle did not finish within {max_steps} step calls")
        current = _request_json(
            "POST",
            f"{base_url}/api/battle/step",
            {"session_id": session_id, "ticks": step_ticks},
        )
        _expect(current.get("ok") is True, "step ok")
        _expect("next_event_index" in current, "step next_event_index")
        steps += 1

    final_snapshot = _expect_dict(current.get("snapshot"), "final snapshot")
    result = _expect_dict(final_snapshot.get("result"), "final result")
    winner = _expect_str(result.get("winner"), "winner")
    reason = _expect_str(result.get("reason"), "reason")
    end_tick = _expect_int(result.get("end_tick"), "end_tick")

    all_events = _request_json(
        "GET",
        f"{base_url}/api/battle/events?session_id={parse.quote(session_id)}&since=0",
    )
    _expect(all_events.get("ok") is True, "events ok")
    event_list = _expect_list(all_events.get("events"), "events list")
    _expect(any(event.get("type") == "battle_end" for event in event_list), "battle_end event")
    next_event_index = _expect_int(all_events.get("next_event_index"), "events next_event_index")

    snapshot_response = _request_json(
        "GET",
        f"{base_url}/api/battle/snapshot?session_id={parse.quote(session_id)}",
    )
    _expect(snapshot_response.get("ok") is True, "snapshot ok")
    _expect_dict(snapshot_response.get("snapshot"), "snapshot payload")

    reset = _request_json("POST", f"{base_url}/api/battle/reset", {"session_id": session_id})
    _expect(reset.get("ok") is True, "reset ok")

    return {
        "service": health.get("service"),
        "session_id": session_id,
        "start_events": len(events),
        "steps": steps,
        "winner": winner,
        "reason": reason,
        "end_tick": end_tick,
        "events": len(event_list),
        "next_event_index": next_event_index,
    }


class SmokeError(Exception):
    pass


def _request_json(method: str, url: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req, timeout=5) as response:
            raw = response.read().decode("utf-8")
    except error.URLError as exc:
        raise SmokeError(f"could not reach {url}: {exc}") from exc
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SmokeError(f"{url}: invalid JSON response: {exc.msg}") from exc
    if not isinstance(decoded, dict):
        raise SmokeError(f"{url}: response must be an object")
    if decoded.get("ok") is False:
        raise SmokeError(f"{url}: {decoded.get('error')}")
    return decoded


def _expect(condition: bool, label: str) -> None:
    if not condition:
        raise SmokeError(f"expected {label}")


def _expect_dict(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise SmokeError(f"expected {label}")
    return value


def _expect_list(value: Any, label: str) -> list:
    if not isinstance(value, list):
        raise SmokeError(f"expected {label}")
    return value


def _expect_str(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise SmokeError(f"expected {label}")
    return value


def _expect_int(value: Any, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise SmokeError(f"expected {label}")
    return value


if __name__ == "__main__":
    raise SystemExit(main())
