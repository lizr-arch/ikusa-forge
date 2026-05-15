# System Overview v0.1

## Architecture

```text
config/source/*.xlsx
  -> tools/export_xlsx_to_json.py
config/generated/*.json
  -> sim-python/ikusa_sim
runs/<battle_id>/replay.json
runs/<battle_id>/battle_report.json
  -> web-viewer
  -> host-csharp
```

## Main modules

| Module | Responsibility |
|---|---|
| Config exporter | Convert xlsx source data into runtime JSON |
| Config validator | Detect invalid ids, missing references, bad numbers |
| Python simulator | Run deterministic battle and emit event stream |
| Report generator | Summarize damage, tanking, kills, triggers, key moments |
| C# host | Execute battle run and read outputs |
| HTML viewer | Play replay and inspect timeline/report |

## Simulator module boundaries

```text
battle.py       battle loop
unit.py         unit state and stat calculation
weapon.py       weapon state and attack data
skill.py        skill trigger and effect resolution
targeting.py    target selection
formation.py    formation bonus
synergy.py      tag/synergy activation
events.py       event model and serialization
rng.py          deterministic random wrapper
report.py       report generation
```

## Event stream first

The simulator must emit events rather than directly controlling visuals.

Good:

```json
{
  "tick": 120,
  "type": "damage",
  "source": "ally_samurai_01",
  "target": "enemy_bandit_02",
  "amount": 18,
  "reason": "katana_slash"
}
```

Bad:

```text
Move HTML sprite directly from Python simulator.
```

## Future migration path

Phase 1:

```text
C# -> Python subprocess -> replay/report
```

Phase 2:

```text
Godot C# -> replay/report viewer
```

Phase 3 candidate:

```text
C# -> Python.NET embedded Python
```

Phase 4 candidate, only if needed:

```text
Python combat core -> C# combat core
```
