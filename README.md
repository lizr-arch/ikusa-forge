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
- Combat System Pack / 战斗系统包（`status_apply`、`skill_cooldown`、`action_scheduled`、`victory_explanation` 可在 replay/report/viewer 中检查）
- Demo One-Click and Scenarios / 一键 Demo 与多场景（viewer 可从静态 Scenario Manifest / 场景清单加载 Curated Fixtures / 固化样例数据，同时保留手动 file input）
- Live Combat Runtime Foundation / 实时战斗运行时基础（`BattleSession / 战斗会话`、`step_battle_session / 单步推进`、`Battle Snapshot / 战斗状态快照`、`Event Buffer / 事件缓冲`，同时保留 `run_basic_combat` 兼容入口）
- Live Combat API / 实时战斗 API（Python 标准库 Local HTTP Server / 本地 HTTP 服务，提供 start/step/snapshot/events/reset 端点）
- HTML Live Mode / HTML 实时模式（`Live Combat API / 实时战斗 API` + HTTP polling，支持 `start/step/pause/resume/reset`）
- Live Battle Visual Polish / 实时战斗视觉打磨（Battlefield-first layout / 战场优先布局，HP 条、行动条、伤害跳字、胜负横幅）
- Live Pixi Battlefield Renderer / PixiJS 实时战场渲染器（主战场使用 PixiJS，DOM 继续负责控制、阵容、战报与性能）
- Realtime Spatial Combat Foundation / 实时空间战斗基础（Continuous Position / 连续坐标、Movement Intent / 移动意图、Target Acquisition / 寻敌、Attack Range / 攻击范围、Unit Movement Event / 单位移动事件）
- Combat Architecture Formalization / 战斗架构正式化（Unit FSM / 单位状态机、Decision Models / 决策模型、Action Pipeline / 行动管线骨架、Combat State / 战斗状态）
- Formation and Engagement System / 编队与接敌系统（Formation Anchor / 编队锚点、Group Advance / 编队推进、Engagement Pairing / 接敌配对、Melee Engagement Lock / 近战接敌锁定、Ranged Hold Distance / 远程保持距离、Separation / 单位分离）
- Action Pipeline Migration / 行动管线迁移（attack/skill/damage/status/cooldown/death 结算统一迁入管线）
- Pipeline Hardening and Status Lifecycle / 管线加固与状态生命周期（行动调度统一迁移、`battle_start` / 战斗开始技能、反应技能、`status_expire` / 状态过期）

Phase 1 Demo Package / 第一阶段演示包 / Phase 2 Tactical Depth notes are available at:

- `docs/process/phase-1-demo-package.md`
- `docs/process/phase-1-summary.md`
- `docs/process/tactical-depth-pack-v0.1.md`
- `docs/process/ci-workflow-v0.1.md`
- `docs/process/combat-behavior-pack-v0.1.md`
- `docs/process/combat-system-pack-v0.1.md`
- `docs/process/demo-one-click-and-scenarios-v0.1.md`
- `docs/process/live-combat-runtime-foundation-v0.1.md`
- `docs/process/live-combat-api-v0.1.md`
- `docs/process/live-battle-visual-polish-v0.1.md`
- `docs/architecture/combat-architecture-v0.1.md`
- `docs/process/combat-architecture-formalization-v0.1.md`
- `docs/process/formation-and-engagement-system-v0.1.md`
- `docs/process/action-pipeline-migration-v0.1.md`
- `docs/process/pipeline-hardening-and-status-lifecycle-v0.1.md`

Quick start for a full demo run / 一次完整演示最简命令:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003
python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples
python tools/run_live_api_smoke.py --config config/generated --battle demo_001 --seed 1001
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
CI also regenerates Scenario Manifest / 场景清单 and Curated Fixtures / 固化样例数据, then runs `git diff --exit-code -- web-viewer/public/samples` to prove committed samples are fresh.
CI also runs Live Combat API / 实时战斗 API smoke with a managed local server process.
- Viewer smoke now also checks Live Battle Visual Polish / 实时战斗视觉打磨 and Realtime Spatial Combat Foundation / 实时空间战斗基础（unit tokens、HP bar / 血条、action bar / 行动条、可见效果、胜负横幅、连续坐标移动）。

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
Click Load Baseline Demo / 加载默认 Demo to load:
web-viewer/public/samples/demo_001/replay.json
web-viewer/public/samples/demo_001/battle_report.json
```

Manual file input / 手动文件输入 remains available for:

```text
runs/demo_001/replay.json
runs/demo_001/battle_report.json
```

The viewer keeps manual file inputs and now shows Scenario Selector / 场景选择器, Scenario Summary / 场景摘要, Demo Load Guidance / Demo 加载引导, Battle Summary / 战斗摘要, Event Highlight / 事件高亮, Report-to-Board Link / 战报到棋盘联动, and Key Moments navigation / 关键时刻跳转 for the generated `demo_001` run.
It also surfaces Combat System Pack / 战斗系统包 evidence: active statuses / 当前状态, skill cooldowns / 技能冷却, next action tick / 下一行动 tick, and victory explanation / 胜负解释.

The simulator also exposes Live Combat Runtime / 实时战斗运行时 primitives:

- `BattleSession / 战斗会话`
- `step_battle_session / 单步推进`
- `step_until_finished / 推进到结束`
- `build_battle_snapshot / 构建战斗状态快照`
- `get_events_since / 读取事件缓冲`

The simulator also exposes these runtime primitives through a local Live Combat API / 实时战斗 API:

```bash
python tools/run_live_api.py --config config/generated --host 127.0.0.1 --port 8765
python tools/smoke_live_api.py --host 127.0.0.1 --port 8765 --battle demo_001 --seed 1001
```

The API is a Python standard-library Local HTTP Server / 本地 HTTP 服务 for external clients.
HTML Live Mode / HTML 实时模式 now consumes this API directly with HTTP polling.
The combat runtime now uses Realtime Spatial Combat / 实时空间战斗 fields, so Live Mode / 实时模式 shows units moving through Continuous Position / 连续坐标 before they attack in Attack Range / 攻击范围; the spatial helpers live in `sim-python/ikusa_sim/spatial_combat.py`, and report summaries include move / target / range / engage counters.

For local HTML Live Mode, the API runs on localhost and returns local development CORS headers
(`Access-Control-Allow-Origin: *`, `Access-Control-Allow-Methods: GET, POST, OPTIONS`,
`Access-Control-Allow-Headers: Content-Type`) so it can be called from
`http://127.0.0.1:5173` / `http://localhost:5173`.
Keep this CORS behavior local-only and avoid exposing it on untrusted networks.

HTML Live Mode usage:

```bash
python tools/run_live_api.py --config config/generated --host 127.0.0.1 --port 8765
cd web-viewer
npm install
npm run dev
```

Then in the Live Mode / 实时模式 panel:

- click `Start Live Battle（开始实时战斗）`
- set `Speed（速度）`
- observe `Live Status（实时状态）` and `Session ID（会话 ID）`

The live battlefield is rendered by PixiJS, while the surrounding controls, roster, report, and performance panels stay in DOM.

When the API is not running, the viewer shows:

- `Live API unavailable（实时 API 不可用）`

Frontend verification:

```bash
cd web-viewer
npm install
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
