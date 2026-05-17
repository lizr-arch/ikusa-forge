"""Basic combat compatibility facade for Ikusa Forge.

The live runtime is implemented in battle_session.py. This module keeps the
existing run_basic_combat entry point and private test hooks stable.
"""

from typing import List, Tuple

from ikusa_sim.battle_session import (
    _run_tick,
    create_battle_session,
    initialize_battle_session,
    step_until_finished,
)
from ikusa_sim.events import BattleEvent
from ikusa_sim.models import ConfigBundle
from ikusa_sim.runtime_models import BattleState


def run_basic_combat(
    config: ConfigBundle,
    battle_id: str,
    seed: int,
) -> Tuple[BattleState, List[BattleEvent]]:
    session = create_battle_session(config, battle_id, seed)
    initialize_battle_session(session)
    step_until_finished(session)
    return session.state, session.events


__all__ = ["_run_tick", "run_basic_combat"]
