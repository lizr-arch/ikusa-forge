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
    total_modifiers = 0
    formation_modifiers = 0
    synergy_modifiers = 0
    total_status_applied = 0
    total_status_expired = 0
    total_skill_cooldowns = 0
    total_actions_scheduled = 0
    total_unit_moves = 0
    total_target_acquired = 0
    total_enter_range = 0
    total_engage_start = 0
    total_formation_anchor_updates = 0
    total_engagement_locks = 0
    total_engagement_releases = 0
    total_ranged_holds = 0
    target_reason_counts = {}  # type: Dict[str, int]
    skill_target_reason_counts = {}  # type: Dict[str, int]

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

        if event_type == "attack":
            reason = payload.get("target_reason")
            if isinstance(reason, str) and reason:
                target_reason_counts[reason] = target_reason_counts.get(reason, 0) + 1
            continue

        if event_type == "skill_trigger":
            source = payload.get("source")
            skill = payload.get("skill")
            reason = payload.get("target_reason")
            if isinstance(reason, str) and reason:
                skill_target_reason_counts[reason] = skill_target_reason_counts.get(reason, 0) + 1
            if source and skill:
                unit = _ensure_unit(units, source)
                skill_triggers = unit["skill_triggers"]
                skill_triggers[skill] = skill_triggers.get(skill, 0) + 1
                total_skill_triggers += 1
            continue

        if event_type == "stat_modifier":
            target = payload.get("target")
            stat = payload.get("stat")
            amount = _as_number(payload.get("amount"))
            source_type = payload.get("source_type")
            if target and stat:
                unit = _ensure_unit(units, target)
                stat_bonuses = unit["stat_bonuses"]
                previous = _as_number(stat_bonuses.get(stat))
                stat_bonuses[stat] = previous + amount
                unit["modifiers_received"] = unit.get("modifiers_received", 0) + 1
                total_modifiers += 1
                if source_type == "formation":
                    formation_modifiers += 1
                elif source_type == "synergy":
                    synergy_modifiers += 1
            continue

        if event_type == "status_apply":
            target = payload.get("target")
            if target:
                _ensure_unit(units, target)["statuses_applied"] += 1
                total_status_applied += 1
            continue

        if event_type == "status_expire":
            target = payload.get("target")
            if target:
                _ensure_unit(units, target)["statuses_expired"] += 1
                total_status_expired += 1
            continue

        if event_type == "skill_cooldown":
            source = payload.get("source")
            if source:
                _ensure_unit(units, source)["cooldowns_started"] += 1
                total_skill_cooldowns += 1
            continue

        if event_type == "action_scheduled":
            unit_id = payload.get("unit")
            if unit_id:
                unit = _ensure_unit(units, unit_id)
                unit["actions_taken"] += 1
                unit["last_next_action_tick"] = _as_optional_int(payload.get("next_action_tick"))
                total_actions_scheduled += 1
            continue

        if event_type == "unit_move":
            unit_id = payload.get("unit")
            if unit_id:
                _ensure_unit(units, unit_id)["moves"] += 1
                total_unit_moves += 1
            continue

        if event_type == "target_acquired":
            unit_id = payload.get("unit")
            if unit_id:
                _ensure_unit(units, unit_id)["target_acquired"] += 1
                total_target_acquired += 1
            continue

        if event_type == "enter_range":
            unit_id = payload.get("unit")
            if unit_id:
                _ensure_unit(units, unit_id)["entered_range"] += 1
                total_enter_range += 1
            continue

        if event_type == "engage_start":
            unit_id = payload.get("unit")
            if unit_id:
                _ensure_unit(units, unit_id)["engagements_started"] += 1
                total_engage_start += 1
            continue

        if event_type == "formation_anchor_update":
            unit_id = payload.get("unit")
            if unit_id:
                _ensure_unit(units, unit_id)["formation_anchor_updates"] += 1
                total_formation_anchor_updates += 1
            continue

        if event_type == "engagement_lock":
            unit_id = payload.get("unit")
            if unit_id:
                _ensure_unit(units, unit_id)["engagement_locks"] += 1
                total_engagement_locks += 1
            continue

        if event_type == "engagement_release":
            unit_id = payload.get("unit")
            if unit_id:
                _ensure_unit(units, unit_id)["engagement_releases"] += 1
                total_engagement_releases += 1
            continue

        if event_type == "ranged_hold":
            unit_id = payload.get("unit")
            if unit_id:
                _ensure_unit(units, unit_id)["ranged_holds"] += 1
                total_ranged_holds += 1
            continue

        if event_type == "battle_end":
            battle_end = payload
            key_moments.append(_battle_end_key_moment(event, payload))

    result = _report_result(metadata, battle_end)
    victory_explanation = _victory_explanation(result, battle_end)
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
            "total_modifiers": total_modifiers,
            "formation_modifiers": formation_modifiers,
            "synergy_modifiers": synergy_modifiers,
            "total_status_applied": total_status_applied,
            "total_status_expired": total_status_expired,
            "total_skill_cooldowns": total_skill_cooldowns,
            "total_actions_scheduled": total_actions_scheduled,
            "total_unit_moves": total_unit_moves,
            "total_target_acquired": total_target_acquired,
            "total_enter_range": total_enter_range,
            "total_engage_start": total_engage_start,
            "target_reason_counts": target_reason_counts,
            "skill_target_reason_counts": skill_target_reason_counts,
            "total_formation_anchor_updates": total_formation_anchor_updates,
            "total_engagement_locks": total_engagement_locks,
            "total_engagement_releases": total_engagement_releases,
            "total_ranged_holds": total_ranged_holds,
        },
        "victory_explanation": victory_explanation,
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
            "modifiers_received": 0,
            "stat_bonuses": {},
            "statuses_applied": 0,
            "statuses_expired": 0,
            "cooldowns_started": 0,
            "actions_taken": 0,
            "last_next_action_tick": None,
            "moves": 0,
            "target_acquired": 0,
            "entered_range": 0,
            "engagements_started": 0,
            "formation_anchor_updates": 0,
            "engagement_locks": 0,
            "engagement_releases": 0,
            "ranged_holds": 0,
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
        "summary": payload.get("summary") or f"Battle ended with winner {winner} by {reason}",
    }


def _victory_explanation(
    result: Dict[str, Any],
    battle_end: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    payload = battle_end or {}
    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary:
        summary = (
            f"Battle ended with winner {result.get('winner')} by {result.get('reason')} "
            f"at tick {result.get('end_tick')}"
        )
    return {
        "winner": result.get("winner"),
        "reason": result.get("reason"),
        "end_tick": result.get("end_tick"),
        "winner_alive": payload.get("winner_alive"),
        "loser_alive": payload.get("loser_alive"),
        "winner_total_hp": payload.get("winner_total_hp"),
        "loser_total_hp": payload.get("loser_total_hp"),
        "summary": summary,
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


def _as_optional_int(value: Any) -> Optional[int]:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def _as_number(value: Any) -> float:
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, int):
        return float(value)
    if isinstance(value, float):
        return value
    return 0.0
