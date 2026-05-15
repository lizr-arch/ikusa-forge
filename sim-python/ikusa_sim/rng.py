"""Battle-scoped deterministic RNG wrapper."""

import random


class BattleRng:
    """Battle-scoped RNG wrapper; do not use global random for simulation."""

    def __init__(self, seed: int):
        self.seed = seed
        self._rng = random.Random(seed)

    def random(self) -> float:
        return self._rng.random()

    def randint(self, start: int, end: int) -> int:
        return self._rng.randint(start, end)
