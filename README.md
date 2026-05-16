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

Current Python simulator status:

- deterministic battle skeleton / 确定性战斗骨架
- Basic Combat Rules / 基础战斗规则
- Minimal Skill Triggers / 最小技能触发
- `skill_trigger event / 技能触发事件`
- damage reason / 伤害原因 in replay events / 回放事件
- Replay Report / 回放与战报
- `battle_report.json / 战报 JSON`
- SVG Replay Viewer / SVG 回放调试器

Still future work:

- synergy application / 羁绊应用
- formation bonus application / 阵型加成应用
- C# host / C# 宿主
- Godot
- xlsx adapter / xlsx 适配器

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
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic

dotnet run --project host-csharp/IkusaForge.Host -- --battle demo_001 --seed 1001
```

Start the SVG Replay Viewer / SVG 回放调试器:

```bash
cd web-viewer
npm install
npm run dev
```

Then load:

```text
runs/demo_001/replay.json
runs/demo_001/battle_report.json
```

Frontend verification:

```bash
cd web-viewer
npm run typecheck
npm run build
```
