# Ikusa Forge

**Ikusa Forge** is a formation auto-battle lab.

The goal is to prototype, simulate, replay, and explain squad-based tactical combat before committing to a full Godot implementation.

## Core idea

```text
Config data
  -> Python combat simulator
  -> replay.json / battle_report.json
  -> HTML replay debugger
  -> C# host / future Godot integration
```

## Phase 1 target

Phase 1 is **not** a finished game. It is a combat validation lab.

Success means:

- change formation -> battle result changes visibly
- change weapon -> skill / damage profile changes visibly
- fixed seed -> deterministic replay
- replay can be inspected in HTML
- battle report explains the main reason for win/loss
- C# host can invoke the Python simulator and read outputs

## Planned stack

| Layer | Technology | Responsibility |
|---|---|---|
| Host | C# / .NET | Execute battle runs, manage paths, read replay/report DTOs |
| Combat core | Python | Rules, targeting, skills, damage, synergies, deterministic simulation |
| Config | xlsx -> JSON | Designer-editable source data and runtime data |
| Debug view | HTML / JS | Replay playback, event timeline, battle report |
| Final client | Godot C# | Later playable shell and presentation layer |

## First command flow

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --out runs/demo_001

dotnet run --project host-csharp/IkusaForge.Host -- --battle demo_001 --seed 1001
```

Open:

```text
web-viewer/index.html
```

Then load:

```text
runs/demo_001/replay.json
runs/demo_001/battle_report.json
```
