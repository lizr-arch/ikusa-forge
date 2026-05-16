"""Synergy resolver for phase 2 tactical depth pack."""

from typing import Callable, Dict, Iterable, List, Optional, Sequence, Union

from ikusa_sim import models as config_models
from ikusa_sim.events import BattleEvent
from ikusa_sim.combat_rules import attack_interval_to_ticks
from ikusa_sim.runtime_models import BattleState, UnitState


SynergyEffect = Callable[
    [Sequence[UnitState], config_models.SynergyDef, BattleState, List[BattleEvent]], None
]


def apply_synergies(
    state: BattleState,
    config: "config_models.ConfigBundle",
    events: List[BattleEvent],
) -> None:
    """Apply side-local synergy modifiers after formations and before on-battle-start skills."""
    units_by_side = {
        "ally": [unit for unit in state.units if unit.side == "ally"],
        "enemy": [unit for unit in state.units if unit.side == "enemy"],
    }

    for _synergy_id, synergy in config.synergies.items():
        if synergy.scope != "matching_units":
            continue
        handler = SYNERGY_RULES.get(_synergy_id)
        if handler is None:
            continue
        for side_units in units_by_side.values():
            handler(side_units, synergy, state, events)


def _apply_stat_modifier(
    source: str,
    source_type: str,
    units: Sequence[UnitState],
    stat: str,
    amount: Union[int, float],
    reason: str,
    state: BattleState,
    events: List[BattleEvent],
) -> None:
    for unit in sorted(units, key=lambda item: item.instance_id):
        applied = False
        if stat == "atk":
            unit.atk += int(round(amount))
            applied = True
        elif stat == "defense":
            unit.defense += int(round(amount))
            applied = True
        elif stat == "range":
            unit.range += int(round(amount))
            applied = True
        elif stat == "hp":
            unit.base_hp += int(round(amount))
            unit.hp += int(round(amount))
            applied = True
        elif stat == "attack_interval_delta":
            unit.base_attack_interval += float(amount)
            if unit.action_interval_ticks > 0:
                unit.action_interval_ticks = attack_interval_to_ticks(
                    unit.base_attack_interval,
                    state.tick_rate,
                )
            unit.next_action_tick = max(0, unit.next_action_tick)
            applied = True

        if not applied:
            continue

        events.append(
            BattleEvent(
                tick=0,
                event_id=_next_event_id(state),
                type="stat_modifier",
                payload={
                    "source": source,
                    "source_type": source_type,
                    "target": unit.instance_id,
                    "stat": stat,
                    "amount": amount,
                    "reason": reason,
                },
            )
        )


def _matching_unit_count(units: Sequence[UnitState], tags: Iterable[str]) -> int:
    tag_set = set(tags)
    return sum(1 for unit in units if tag_set.intersection(unit.tags))


def _filter_units_by_tags(units: Sequence[UnitState], tags: Iterable[str]) -> List[UnitState]:
    tag_set = set(tags)
    return [unit for unit in units if tag_set.intersection(unit.tags)]


def _filter_units_by_ids(units: Sequence[UnitState], ids: Iterable[str]) -> List[UnitState]:
    want = set(ids)
    return [unit for unit in units if unit.unit_def_id in want]


def _apply_thresholded_bonuses(
    units: Sequence[UnitState],
    source_id: str,
    state: BattleState,
    events: List[BattleEvent],
    thresholds: Dict[str, Dict[str, float]],
    targets_selector: Callable[[], Sequence[UnitState]],
) -> None:
    if not units:
        return

    count = len(units)
    thresholds_map: Dict[int, Dict[str, float]] = {}
    for key, value in thresholds.items():
        if not isinstance(key, str):
            continue
        try:
            parsed = int(key)
        except ValueError:
            continue
        if isinstance(value, dict):
            thresholds_map[parsed] = value

    matched_threshold = _max_threshold(thresholds_map, count)
    if matched_threshold is None:
        return

    bonus_targets = targets_selector()
    if not bonus_targets:
        return

    reason = f"{source_id}:threshold_{matched_threshold}"
    source = f"synergy:{source_id}"
    for stat, value in thresholds_map[matched_threshold].items():
        if not isinstance(value, (int, float)):
            continue
        if not _is_supported_stat(stat):
            continue
        _apply_stat_modifier(
            source=source,
            source_type="synergy",
            units=bonus_targets,
            stat=stat,
            amount=value,
            reason=reason,
            state=state,
            events=events,
        )


def _is_supported_stat(stat: str) -> bool:
    return stat in {"atk", "defense", "range", "hp", "attack_interval_delta"}


def _max_threshold(
    threshold_map: Dict[int, Dict[str, float]],
    count: int,
) -> Optional[int]:
    matched: Optional[int] = None
    for threshold in sorted(threshold_map):
        if threshold <= count:
            matched = threshold
    return matched


def _spear_wall(side_units: Sequence[UnitState], synergy: config_models.SynergyDef, state: BattleState, events: List[BattleEvent]) -> None:
    matched_units = _filter_units_by_tags(side_units, ["spear"])
    _apply_thresholded_bonuses(
        matched_units,
        "spear_wall",
        state,
        events,
        synergy.thresholds,
        targets_selector=lambda: matched_units,
    )


def _arrow_volley(side_units: Sequence[UnitState], synergy: config_models.SynergyDef, state: BattleState, events: List[BattleEvent]) -> None:
    matched_units = _filter_units_by_tags(side_units, ["bow"])
    _apply_thresholded_bonuses(
        matched_units,
        "arrow_volley",
        state,
        events,
        synergy.thresholds,
        targets_selector=lambda: matched_units,
    )


def _blade_dance(side_units: Sequence[UnitState], synergy: config_models.SynergyDef, state: BattleState, events: List[BattleEvent]) -> None:
    matched_units = _filter_units_by_tags(side_units, ["katana"])
    # blade_dance is proposed id for katana pairings; sample data uses duelist_honor.
    _apply_thresholded_bonuses(
        matched_units,
        "blade_dance",
        state,
        events,
        synergy.thresholds,
        targets_selector=lambda: matched_units,
    )


def _shadow_pair(side_units: Sequence[UnitState], synergy: config_models.SynergyDef, state: BattleState, events: List[BattleEvent]) -> None:
    matched_units = _filter_units_by_tags(side_units, ["ninja", "ninja_tool"])
    if not matched_units:
        return
    _apply_thresholded_bonuses(
        matched_units,
        "shadow_pair",
        state,
        events,
        synergy.thresholds,
        targets_selector=lambda: matched_units,
    )


def _banner_core(
    side_units: Sequence[UnitState],
    synergy: config_models.SynergyDef,
    state: BattleState,
    events: List[BattleEvent],
) -> None:
    # banner + any 2 allies requirement simplified with side-local count check.
    if len(side_units) < 3:
        return
    matched_units = _filter_units_by_tags(side_units, ["banner"])
    if not matched_units:
        return
    _apply_thresholded_bonuses(
        matched_units,
        "banner_core",
        state,
        events,
        synergy.thresholds,
        targets_selector=lambda: side_units,
    )


def _mixed_arms(
    side_units: Sequence[UnitState],
    synergy: config_models.SynergyDef,
    state: BattleState,
    events: List[BattleEvent],
) -> None:
    if (
        _matching_unit_count(side_units, ["spear"]) >= 1
        and _matching_unit_count(side_units, ["bow"]) >= 1
        and _matching_unit_count(side_units, ["katana"]) >= 1
    ):
        _apply_thresholded_bonuses(
            side_units,
            "mixed_arms",
            state,
            events,
            synergy.thresholds,
            targets_selector=lambda: side_units,
        )


def _duelist_honor(side_units: Sequence[UnitState], synergy: config_models.SynergyDef, state: BattleState, events: List[BattleEvent]) -> None:
    # Existing sample data alias for katana pair-oriented synergy.
    matched_units = _filter_units_by_tags(side_units, ["samurai"])
    if not matched_units:
        return
    _apply_thresholded_bonuses(
        matched_units,
        "duelist_honor",
        state,
        events,
        synergy.thresholds,
        targets_selector=lambda: matched_units,
    )


def _massed_troops(side_units: Sequence[UnitState], synergy: config_models.SynergyDef, state: BattleState, events: List[BattleEvent]) -> None:
    matched_units = _filter_units_by_tags(side_units, ["ashigaru"])
    if not matched_units:
        return
    _apply_thresholded_bonuses(
        matched_units,
        "massed_troops",
        state,
        events,
        synergy.thresholds,
        targets_selector=lambda: matched_units,
    )


def _flank_opening(side_units: Sequence[UnitState], synergy: config_models.SynergyDef, state: BattleState, events: List[BattleEvent]) -> None:
    matched_units = [unit for unit in side_units if "left_flank" in unit.tags or "right_flank" in unit.tags]
    if not matched_units:
        return
    _apply_thresholded_bonuses(
        matched_units,
        "flank_opening",
        state,
        events,
        synergy.thresholds,
        targets_selector=lambda: matched_units,
    )


def _next_event_id(state: BattleState) -> str:
    event_id = f"evt_{state._next_event_number:06d}"
    state._next_event_number += 1
    return event_id


SYNERGY_RULES: Dict[str, SynergyEffect] = {
    "spear_wall": _spear_wall,
    "arrow_volley": _arrow_volley,
    "duelist_honor": _duelist_honor,
    "sword_rhythm": _blade_dance,
    "massed_troops": _massed_troops,
    "flank_opening": _flank_opening,
    # Optional proposal aliases; only run when present in config.
    "blade_dance": _blade_dance,
    "shadow_pair": _shadow_pair,
    "banner_core": _banner_core,
    "mixed_arms": _mixed_arms,
}
