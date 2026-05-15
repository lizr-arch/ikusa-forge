"""Event-derived battle report generation for Ikusa Forge Phase 1."""

from typing import Any, Dict, List, Optional, Sequence


def build_battle_report(
    replay_doc: Dict[str, Any],
    timeline_events: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    metadata = replay_doc.get("metadata", {})
    return build_battle_report_from_events(metadata, timeline_events)


def build_battle_report_from_events(
    metadata: Dict[str, Any],
    events: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    units = {}  # type: Dict[str, Dict[str, Any]]
    key_moments = []  # type: List[Dict[str, Any]]
    last_damage_source_by_target = {}  # type: Dict[str, Optional[str]]
    battle_end = None  # type: Optional[Dict[str, Any]]

    total_damage = 0
    total_kills = 0
    total_skill_triggers = 0

    for event in events:
        event_type = event.get("type")
        payload = event.get("payload", {})

        if event_type == "unit_spawn":
            unit = payload.get("unit", {})
            unit_id = unit.get("instance_id")
            if unit_id:
                _ensure_unit(units, unit_id)
            continue

        if event_type == "damage":
            source = payload.get("source")
            target = payload.get("target")
            amount = _as_int(payload.get("amount"))
            total_damage += amount
            if source:
                _ensure_unit(units, source)["damage_done"] += amount
            if target:
                _ensure_unit(units, target)["damage_taken"] += amount
                last_damage_source_by_target[target] = source
            continue

        if event_type == "death":
            dead_unit = payload.get("unit")
            killer = last_damage_source_by_target.get(dead_unit)
            if dead_unit:
                _ensure_unit(units, dead_unit)["deaths"] += 1
            if killer:
                _ensure_unit(units, killer)["kills"] += 1
                total_kills += 1
            key_moments.append(_death_key_moment(event, dead_unit, killer))
            continue

        if event_type == "skill_trigger":
            source = payload.get("source")
            skill = payload.get("skill")
            if source and skill:
                unit = _ensure_unit(units, source)
                skill_triggers = unit["skill_triggers"]
                skill_triggers[skill] = skill_triggers.get(skill, 0) + 1
                total_skill_triggers += 1
            continue

        if event_type == "battle_end":
            battle_end = payload
            key_moments.append(_battle_end_key_moment(event, payload))

    result = _report_result(metadata, battle_end)
    return {
        "schema_version": "battle_report.v0.1",
        "battle_id": metadata.get("battle_id"),
        "seed": metadata.get("seed"),
        "winner": result.get("winner"),
        "reason": result.get("reason"),
        "end_tick": result.get("end_tick"),
        "summary": {
            "total_damage": total_damage,
            "total_kills": total_kills,
            "total_skill_triggers": total_skill_triggers,
        },
        "units": units,
        "top_units": {
            "damage_done": _top_units(units, "damage_done"),
            "damage_taken": _top_units(units, "damage_taken"),
            "skill_triggers": _top_skill_trigger_units(units),
        },
        "key_moments": key_moments,
    }


def _ensure_unit(units: Dict[str, Dict[str, Any]], unit_id: str) -> Dict[str, Any]:
    if unit_id not in units:
        units[unit_id] = {
            "damage_done": 0,
            "damage_taken": 0,
            "kills": 0,
            "deaths": 0,
            "skill_triggers": {},
        }
    return units[unit_id]


def _report_result(
    metadata: Dict[str, Any],
    battle_end: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    metadata_result = metadata.get("result")
    if isinstance(metadata_result, dict):
        return {
            "winner": metadata_result.get("winner"),
            "reason": metadata_result.get("reason"),
            "end_tick": metadata_result.get("end_tick"),
        }
    if battle_end:
        return {
            "winner": battle_end.get("winner"),
            "reason": battle_end.get("reason"),
            "end_tick": battle_end.get("end_tick"),
        }
    return {"winner": None, "reason": None, "end_tick": None}


def _death_key_moment(
    event: Dict[str, Any],
    dead_unit: Optional[str],
    killer: Optional[str],
) -> Dict[str, Any]:
    if killer:
        summary = f"{dead_unit} was killed by {killer}"
    else:
        summary = f"{dead_unit} died with no known killer"
    return {
        "tick": event.get("tick"),
        "type": "death",
        "unit": dead_unit,
        "killer": killer,
        "summary": summary,
    }


def _battle_end_key_moment(
    event: Dict[str, Any],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    winner = payload.get("winner")
    reason = payload.get("reason")
    end_tick = payload.get("end_tick", event.get("tick"))
    return {
        "tick": event.get("tick"),
        "type": "battle_end",
        "winner": winner,
        "reason": reason,
        "end_tick": end_tick,
        "summary": f"Battle ended with winner {winner} by {reason}",
    }


def _top_units(units: Dict[str, Dict[str, Any]], field: str, limit: int = 3) -> List[str]:
    ranked = [
        (unit_id, values.get(field, 0))
        for unit_id, values in units.items()
        if values.get(field, 0) > 0
    ]
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return [unit_id for unit_id, _ in ranked[:limit]]


def _top_skill_trigger_units(
    units: Dict[str, Dict[str, Any]],
    limit: int = 3,
) -> List[str]:
    ranked = []
    for unit_id, values in units.items():
        total = sum(values.get("skill_triggers", {}).values())
        if total > 0:
            ranked.append((unit_id, total))
    ranked.sort(key=lambda item: (-item[1], item[0]))
    return [unit_id for unit_id, _ in ranked[:limit]]


def _as_int(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0
