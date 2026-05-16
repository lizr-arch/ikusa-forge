"""Formation bonus resolver for phase 2 tactical depth pack."""

from typing import Callable, Dict, List, Sequence, Tuple

from ikusa_sim.events import BattleEvent
from ikusa_sim.runtime_models import BattleState, UnitState


StatName = str
BonusRule = Tuple[Tuple[str, ...], str, int, str]


def apply_formation_bonuses(state: BattleState, events: List[BattleEvent]) -> None:
    """Apply deterministic formation-based stat modifiers and emit stat_modifier events."""
    if not state.units:
        return

    for formation_id, formation_units in _group_units_by_formation(state.units).items():
        rule_builder = FORMATION_BONUS_RULES.get(formation_id)
        if rule_builder is None:
            continue
        rules = rule_builder()
        for role_targets, stat, amount, reason in rules:
            units = [unit for unit in formation_units if unit.role in role_targets]
            _apply_bonus(
                source=f"formation:{formation_id}",
                source_type="formation",
                units=units,
                stat=stat,
                amount=amount,
                reason=reason,
                state=state,
                events=events,
            )


def _apply_bonus(
    *,
    source: str,
    source_type: str,
    units: Sequence[UnitState],
    stat: StatName,
    amount: int,
    reason: str,
    state: BattleState,
    events: List[BattleEvent],
) -> None:
    if amount == 0 or not units:
        return

    for unit in sorted(units, key=lambda item: item.instance_id):
        _apply_stat_delta(unit, stat, amount)
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


def _group_units_by_formation(units: Sequence[UnitState]) -> Dict[str, List[UnitState]]:
    groups: Dict[str, List[UnitState]] = {}
    for unit in units:
        groups.setdefault(unit.formation_id, []).append(unit)
    return groups


def _apply_stat_delta(unit: UnitState, stat: str, amount: int) -> None:
    if stat == "atk":
        unit.atk += amount
    elif stat == "defense":
        unit.defense += amount
    elif stat == "range":
        unit.range += amount
    else:
        # Unknown stat names are intentionally ignored to keep event payloads permissive.
        return


def _format_event_id(sequence_number: int) -> str:
    return f"evt_{sequence_number:06d}"


def _next_event_id(state: BattleState) -> str:
    event_id = _format_event_id(state._next_event_number)
    state._next_event_number += 1
    return event_id


BonusRuleBuilder = Callable[[], List[BonusRule]]


def _fish_scale_rules() -> List[BonusRule]:
    return [
        (("vanguard", "center"), "atk", 3, "fish_scale:vanguard_center_atk_plus_3"),
    ]


def _crane_wing_rules() -> List[BonusRule]:
    return [
        (("left_flank", "right_flank"), "atk", 2, "crane_wing:flank_pressure"),
        (("support", "left_support", "right_support"), "atk", 1, "crane_wing:flank_pressure_support"),
    ]


def _goose_line_rules() -> List[BonusRule]:
    return [
        (("backline",), "defense", 2, "goose_line:backline_defense_plus_2"),
    ]


FORMATION_BONUS_RULES: Dict[str, BonusRuleBuilder] = {
    "fish_scale": _fish_scale_rules,
    "crane_wing": _crane_wing_rules,
    "goose_line": _goose_line_rules,
}
