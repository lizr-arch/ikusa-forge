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
- C# host contract compatibility is a future goal; it is not implemented yet

Current Python simulator status:

- deterministic battle skeleton / 确定性战斗骨架
- Basic Combat Rules / 基础战斗规则
- Minimal Skill Triggers / 最小技能触发
- `skill_trigger event / 技能触发事件`
- damage reason / 伤害原因 in replay events / 回放事件
- Replay Report / 回放与战报
- `battle_report.json / 战报 JSON`
- SVG Replay Viewer / SVG 回放调试器
- HTML Demo Complete Experience / HTML 最小 Demo 完整体验闭环
- Formation bonus / 阵型加成 与 Synergy application / 羁绊应用（当前 demo 已按 tick 0 一次性应用）
- Report explainability / 报表可解释性（`stat_modifier` 计入回放与战报）

Phase 1 Demo Package / 第一阶段演示包 / Phase 2 Tactical Depth notes are available at:

- `docs/process/phase-1-demo-package.md`
- `docs/process/phase-1-summary.md`
- `docs/process/tactical-depth-pack-v0.1.md`
- `docs/process/ci-workflow-v0.1.md`
- `docs/process/combat-behavior-pack-v0.1.md`

Quick start for a full demo run / 一次完整演示最简命令:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
python -m unittest discover -s sim-python/tests
cd web-viewer
npm install
npm run dev
```

Optional CI parity check / 可选 CI 对齐验证（当前 CI 使用 npm install）:

```bash
cd web-viewer
npm install
npm run typecheck
npm run build
npm run test:e2e
```

CI uses `npm install` now because `npm ci` can fail on optional dependency lockfile churn across Windows/Linux.
`npm ci` is still a goal, but it remains temporarily unavailable until lockfile stabilization.

Still future work:

- C# host / C# 宿主: future goal is to consume the same replay/report contract without changing combat logic
- Godot
- xlsx adapter / xlsx 适配器

## Planned stack

| Layer | Technology | Responsibility |
|---|---|---|
| Host | C# / .NET | Execute battle runs, manage paths, read replay/report DTOs |
| Combat core | Python | Rules, targeting, skills, damage, synergies, deterministic simulation |
| Config | xlsx -> JSON | Designer-editable source data and runtime data |
| Debug view | Vite + TypeScript + native SVG/DOM | Replay playback, event timeline, battle report |
| Final client | Godot C# | Later playable shell and presentation layer |

## First command flow

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001

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

The viewer keeps manual file inputs and now shows Demo Load Guidance / Demo 加载引导, Battle Summary / 战斗摘要, Event Highlight / 事件高亮, Report-to-Board Link / 战报到棋盘联动, and Key Moments navigation / 关键时刻跳转 for the generated `demo_001` run.

Frontend verification:

```bash
cd web-viewer
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

Review docs:

- `docs/process/phase-1-mvp-review.md`
- `docs/process/viewer-smoke-checklist.md`
- `docs/process/viewer-browser-smoke-v0.1.md`
- `docs/process/html-demo-complete-experience-v0.1.md`
