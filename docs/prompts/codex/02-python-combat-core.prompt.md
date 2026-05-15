# Codex Prompt: Python Combat Core v0.1

You are working in the `ikusa-forge` repository.

Goal: implement a deterministic Python combat simulator.

Read:

- `AGENTS.md`
- `docs/design/01-combat-pillars.md`
- `docs/design/02-mvp-scope-v0.1.md`
- `docs/design/04-system-overview.md`
- `docs/process/02-review-checklist.md`

Implement modules:

```text
sim-python/ikusa_sim/
  battle.py
  unit.py
  weapon.py
  skill.py
  targeting.py
  formation.py
  synergy.py
  events.py
  rng.py
  report.py
```

Implement tool:

```text
tools/run_demo_battle.py
```

Requirements:

- takes battle id and seed
- loads config/generated JSON
- runs deterministic tick battle
- outputs:
  - `runs/<battle_id>/replay.json`
  - `runs/<battle_id>/battle_report.json`
  - `runs/<battle_id>/debug_timeline.json`
  - `runs/<battle_id>/run_summary.md`

Minimum combat behavior:

- unit hp, atk, defense, range, attack interval
- target selection
- basic attack
- at least 3 skill effects
- death
- victory/defeat/timeout
- simple formation or synergy bonus

Event stream requirements:

- battle_start
- unit_spawn
- attack
- damage
- skill_trigger
- death
- battle_end

Tests:

```text
sim-python/tests/test_damage.py
sim-python/tests/test_targeting.py
sim-python/tests/test_replay_determinism.py
sim-python/tests/test_synergy.py
```

Determinism requirement:

Same seed + same config + same encounter must produce identical replay JSON.

Completion report must include:

- changed files
- exact run command
- test command
- generated artifact paths
- one short explanation of why the winner won
- known limitations
