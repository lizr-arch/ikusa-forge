"""Battle event helpers for Ikusa Forge Phase 1."""

from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Sequence


@dataclass(frozen=True)
class BattleEvent:
    tick: int
    event_id: str
    type: str
    payload: Dict[str, Any]


def event_to_dict(event: BattleEvent) -> Dict[str, Any]:
    return asdict(event)


def events_to_tick_groups(events: Sequence[BattleEvent]) -> List[Dict[str, Any]]:
    groups = []  # type: List[Dict[str, Any]]
    index_by_tick = {}  # type: Dict[int, int]

    for event in events:
        if event.tick not in index_by_tick:
            index_by_tick[event.tick] = len(groups)
            groups.append({"tick": event.tick, "events": []})
        groups[index_by_tick[event.tick]]["events"].append(event_to_dict(event))

    return groups
