# SVG Replay Viewer / SVG 回放调试器 v0.1

This stage adds a read-only SVG Replay Viewer / SVG 回放调试器 for Phase 1 replay inspection.

## Goal / 目标

The viewer loads local `replay.json / 回放 JSON` and `battle_report.json / 战报 JSON`, reconstructs a Visual State / 可视化状态 from replay events, and renders combat state without running simulator logic / 模拟器逻辑.

## Scope / 范围

Implemented:

- Vite + TypeScript app in `web-viewer`.
- Native SVG/DOM rendering, no React/Vue/game rendering framework.
- Local file loading with browser `File` inputs.
- SVG Board / SVG 棋盘 for `ally/enemy` 4x3 sides.
- Timeline / 时间线 with event filters.
- Playback Controls / 播放控制 for play/pause, step tick, previous/next event, tick slider, and speed.
- Report Panel / 战报面板 with winner, reason, totals, top units, unit rows, and key moments.
- Unit Detail Panel / 单位详情面板 with visual state plus report stats.

Not implemented:

- Combat rule changes / 战斗规则修改.
- C# host / C# 宿主.
- Godot gameplay / Godot 玩法.
- Synergy application / 羁绊应用.
- Formation bonus application / 阵型加成应用.
- xlsx adapter / xlsx 适配器.
- Backend server / 后端服务.
- Combat execution inside the viewer / 回放器内执行战斗.

## Data Boundary / 数据边界

The viewer reads:

```text
runs/demo_001/replay.json
runs/demo_001/battle_report.json
```

The viewer does not write config, replay, report, or run output. It does not read xlsx directly and does not modify JSON artifacts.

Runtime dependency direction remains:

```text
config -> simulator -> replay/report -> viewer
```

The forbidden directions remain forbidden:

```text
simulator -> web viewer
simulator -> Godot scene
simulator -> C# UI
```

## Visual State / 可视化状态

`web-viewer/src/replayState.ts` reconstructs state by replaying events from tick 0 to the selected tick or selected event.

Handled event types:

- `battle_start / 战斗开始`: metadata marker.
- `unit_spawn / 单位生成`: creates a visual unit from `payload.unit`.
- `attack / 普通攻击`: records the latest attack line.
- `skill_trigger / 技能触发`: records the latest skill marker and targets.
- `damage / 伤害`: updates target HP and latest damage text.
- `death / 死亡`: marks a unit dead.
- `battle_end / 战斗结束`: records winner, reason, and end tick.

Selected unit state is UI-only. It is not stored in replay data.

## Commands / 命令

Generate sample data:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
```

Run simulator tests:

```bash
python -m unittest discover -s sim-python/tests
```

Install and run the viewer:

```bash
cd web-viewer
npm install
npm run dev
```

Verify the viewer:

```bash
cd web-viewer
npm run typecheck
npm run build
```

Windows Python launcher variants:

```bash
py -3.11 tools/export_xlsx_to_json.py --input config/source --output config/generated
py -3.11 tools/validate_config.py --input config/generated
py -3.11 tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
py -3.11 -m unittest discover -s sim-python/tests
```

## Manual Smoke / 手动冒烟

1. Start `npm run dev` in `web-viewer`.
2. Load `runs/demo_001/replay.json`.
3. Load `runs/demo_001/battle_report.json`.
4. Confirm the board shows ally and enemy units.
5. Confirm tick slider, step tick, previous/next event, timeline filters, report panel, and unit click detail work.
6. Confirm no backend request is required.

## Known Limitations / 已知限制

- The viewer targets the current `battle_replay.v0.1` and `battle_report.v0.1` shapes.
- Playback advances by discrete tick jumps, not smooth animation.
- Visual annotations show the latest applied attack, damage, and skill marker.
- The viewer does not load `debug_timeline.json`; it flattens `replay.ticks[].events[]` directly.
