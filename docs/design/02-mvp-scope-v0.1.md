# MVP Scope v0.1

## Goal

Build a deterministic combat lab that can run and explain one complete formation auto-battle.

## Board

Use a 4x3 grid for each side.

```text
Enemy side      Player side

E E E E         A A A A
E E E E         A A A A
E E E E         A A A A
```

Phase 1 may represent each side in its own 4x3 grid and resolve distance abstractly.

## Unit count

Minimum content:

| Side | Count |
|---|---:|
| Player units | 6 |
| Enemy units | 6 |

## Weapon types

| Weapon | Role |
|---|---|
| Katana | balanced melee |
| Spear | anti-charge / reach |
| Bow | ranged backline |
| Shield | protector / tank |
| Ninja tool | burst / disruption |

## Skills

Minimum 10 skills:

1. Katana Slash
2. Iaijutsu Burst
3. Spear Thrust
4. Brace Counter
5. Bow Shot
6. Focus Fire
7. Shield Guard
8. Intercept
9. Smoke Strike
10. Banner Rally

## Formations

Minimum 3 formations:

| Formation | Intended behavior |
|---|---|
| Fish Scale | strong center push |
| Crane Wing | flanking bonus |
| Goose Line | ranged/backline protection |

## Synergies

Minimum 6 synergies:

| Type | Example |
|---|---|
| Weapon | 2+ spear units activate Spear Wall |
| Weapon | 2+ bow units activate Arrow Volley |
| Weapon | 2+ katana units activate Sword Rhythm |
| Identity | 3+ ashigaru activate Massed Troops |
| Identity | 2+ samurai activate Duelist Honor |
| Formation | flank units gain opening strike |

## Combat mechanics

Required:

- tick loop
- cooldowns
- target selection
- basic attack
- skill trigger
- damage and death
- victory/defeat check
- event log
- battle report

Not required:

- pathfinding
- collision
- animation
- real-time input
- multiplayer
- procedural campaign

## Output artifacts

Each battle run must output:

```text
runs/<battle_id>/
  replay.json
  battle_report.json
  debug_timeline.json
  run_summary.md
```

## Acceptance criteria

- Same seed produces same replay.
- At least one test proves determinism.
- Moving one key unit changes the battle result or report.
- Weapon change affects damage or skill trigger profile.
- HTML viewer can inspect a battle from replay JSON.
- C# host can invoke Python and print battle summary.
