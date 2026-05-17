# Demo One-Click and Scenarios / 一键 Demo 与多场景 v0.1

## Goal / 目标

Demo One-Click / 一键 Demo lowers the cost of opening the SVG Replay Viewer / SVG 回放调试器 for review, demos, and smoke checks. A user can start the web viewer and load a curated sample battle without manually selecting `replay.json` and `battle_report.json`.

Scenario Manifest / 场景清单 and Scenario Selector / 场景选择器 add a small static catalog of sample battles. This is a viewer/demo delivery layer only: it does not change combat rules, config semantics, or simulator determinism.

## Curated Fixtures / 固化样例数据

Curated Fixture / 固化样例数据 is committed under:

```text
web-viewer/public/samples/
```

This directory is intentionally versioned because Vite serves `public/` as static viewer assets. The viewer can therefore fetch sample replay/report JSON files without a backend.

`runs/` remains ignored because it is local run output for ad hoc battles. `config/generated/` remains ignored because runtime config JSON is generated from source data and should be recreated by tools and CI.

Committed fixture paths:

```text
web-viewer/public/samples/manifest.json
web-viewer/public/samples/demo_001/replay.json
web-viewer/public/samples/demo_001/battle_report.json
web-viewer/public/samples/demo_seed_1002/replay.json
web-viewer/public/samples/demo_seed_1002/battle_report.json
web-viewer/public/samples/demo_seed_1003/replay.json
web-viewer/public/samples/demo_seed_1003/battle_report.json
```

Current seed differences are Scenario slots / 场景槽位 for future randomized mechanics. Current combat is deterministic and does not consume randomness in a way that changes this sample outcome, so identical winner/reason/end_tick across these slots is not an error.

## Scenario Manifest / 场景清单

Scenario Manifest / 场景清单 lives at:

```text
web-viewer/public/samples/manifest.json
```

The viewer fetches it from:

```text
/samples/manifest.json
```

Manifest fields:

- `schema_version`: manifest contract version, currently `scenario_manifest.v0.1`.
- `scenarios`: ordered scenario list.
- `id`: stable scenario id used by Scenario Selector / 场景选择器.
- `battle_id`: simulator battle id used to generate the fixture.
- `seed`: simulator seed used to generate the fixture.
- `name`: human-readable scenario name.
- `description`: concise scenario description for the UI.
- `replay_url`: static URL for `replay.json`.
- `report_url`: static URL for `battle_report.json`.
- `expected`: expected `winner` and `reason` used by smoke checks and review.

## Generate Fixtures / 生成样例

Batch Scenario Generation / 批量场景生成 uses only Python standard library plus existing repo modules:

```bash
python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003
```

The generator:

- exports config from `config/source`
- validates `config/generated`
- runs each scenario in `basic` mode
- writes replay/report JSON into `web-viewer/public/samples/<scenario_id>/`
- writes Scenario Manifest / 场景清单 to `web-viewer/public/samples/manifest.json`
- writes stable, formatted JSON so CI can compare committed fixtures against regenerated output

It does not write committed `runs/` artifacts and does not include `debug_timeline.json` or `run_summary.md` in static samples because the viewer does not need them.

## Viewer Flow / 回放器流程

On startup, the viewer attempts to fetch Scenario Manifest / 场景清单 from `/samples/manifest.json`.

If the fetch succeeds:

- Scenario Selector / 场景选择器 is shown.
- Load Baseline Demo / 加载默认 Demo loads `demo_001`.
- Load Scenario / 加载场景 loads the selected scenario.
- The viewer fetches both replay and report JSON, then uses the existing replay/report state pipeline.
- Scenario Summary / 场景摘要 shows scenario id, name, description, winner, reason, end tick, event count, total damage, status applications, cooldowns, and action schedules.

If the manifest fetch fails, manual file input loading remains available. This keeps local file workflows and generated `runs/demo_001` review unchanged.

## Smoke / 冒烟

Static Scenario Smoke / 场景静态冒烟:

```bash
python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples
```

It checks:

- `manifest.json` exists and uses `scenario_manifest.v0.1`
- at least three scenarios exist
- every scenario has replay/report files
- replay schema is `battle_replay.v0.1`
- report schema is `battle_report.v0.1`
- every scenario has winner/reason/end_tick
- `demo_001` includes MVP event types including `status_apply`, `skill_cooldown`, and `action_scheduled`

Browser Smoke / 浏览器冒烟 keeps the manual File Input Loading / 文件输入加载 test and adds One-click Demo / 一键 Demo coverage:

- manifest and Scenario Selector / 场景选择器 visible
- Load Baseline Demo / 加载默认 Demo succeeds
- board shows 12 units
- battle summary shows `ally / enemy_eliminated`
- timeline filters find combat-system events
- report shows Victory Explanation / 胜负解释
- manual replay/report file inputs still exist

## CI Contract / CI 契约

CI regenerates Curated Fixtures / 固化样例数据 and fails if committed fixtures are stale:

```bash
python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003
python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples
git diff --exit-code -- web-viewer/public/samples
```

This makes Scenario Manifest / 场景清单 and Curated Fixture / 固化样例数据 part of the demo contract. Any future combat/report change that alters sample output must intentionally regenerate and commit the updated fixtures.

## Scenario Comparison / 场景对比

Scenario Comparison / 场景对比 is currently limited to comparing static sample outputs by id, seed, summary, and event counts. The viewer does not include a side-by-side comparison UI in this phase.

## Demo Contract / 演示契约

Demo Contract / 演示契约 for this phase:

- viewer can load a curated scenario without manual file input
- manual file input remains available
- samples are static files, not backend responses
- committed samples are reproducible from source config, battle id, and seed
- CI proves committed samples match generator output
- combat rules and skill effects are unchanged

## Not in Scope / 不在范围

- No C# host / 不做 C# 宿主
- No Godot / 不做 Godot
- No xlsx adapter / 不做 xlsx 适配器
- No movement/pathfinding / 不做移动与寻路
- No new combat rules / 不做新战斗规则
- No new skill effects / 不做新技能效果
- No general-purpose DSL / 不做通用 DSL
- No new frontend framework / 不引入新前端框架
- No React / 不引入 React
- No Vue / 不引入 Vue
- No Phaser / 不引入 Phaser
- No PixiJS / 不引入 PixiJS
- No Three.js / 不引入 Three.js
- No visual regression / 不做视觉回归
- No cross-browser matrix / 不做跨浏览器矩阵
