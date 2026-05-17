# Local Development Setup

This repository is currently in Phase 1 Replay Report / 回放与战报 plus SVG Replay Viewer / SVG 回放调试器 v0.1 state.

For a packaged demo flow, see:

- `docs/process/phase-1-demo-package.md`
- `docs/process/phase-1-summary.md`
- `docs/process/tactical-depth-pack-v0.1.md`
- `docs/process/ci-workflow-v0.1.md`

The config pipeline, pure Python runtime model boundary, deterministic replay event stream, Basic Combat Rules / 基础战斗规则, Minimal Skill Triggers / 最小技能触发, Formation bonus / 阵型加成, Synergy application / 羁绊应用, Replay Report / 回放与战报, and read-only SVG Replay Viewer / SVG 回放调试器 exist so later tasks can add a C# subprocess host without mixing responsibilities.

## Expected local tools

- Project target: Python >= 3.10.
- Recommended Python: 3.11 or newer.
- Python 3.6 is no longer supported for the Python combat model layer because it uses standard-library dataclasses and modern typing expectations.
- On Windows, prefer `py -3.11` for all simulator/model commands.
- Node.js and npm for `web-viewer`.
- .NET SDK for the future C# host.
- A modern browser for the SVG Replay Viewer / SVG 回放调试器.

No heavy dependencies are required for the current CSV-first config pipeline. The web viewer uses Vite + TypeScript and native SVG/DOM only.

## Repository layout

```text
config/source/      Designer-editable source data and CSV sample data.
config/generated/   Runtime JSON output; generated files are ignored.
sim-python/         Pure Python combat simulator package and tests.
host-csharp/        Future C# host that invokes Python as a subprocess.
web-viewer/         Local SVG replay debugger.
tools/              Export, validation, inspection, and demo-run scripts.
runs/               Generated battle run output; generated files are ignored.
docs/schema/        JSON schema drafts for runtime config.
```

## Export config

The v0.1 exporter keeps the stable command name planned for xlsx support:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
```

On Windows, prefer the Python launcher when Python 3.11 is installed:

```bash
py -3.11 tools/export_xlsx_to_json.py --input config/source --output config/generated
```

The bare `python` command is kept as a compatibility example for simple local shells.

Current behavior:

- v0.1/v0.1.3 reads CSV sample data from `config/source/sample_data/*.csv`.
- Writes formatted runtime JSON to `config/generated/*.json`.
- Converts configured comma-separated fields into JSON arrays.
- Parses configured JSON cells such as formation patterns and encounter unit lists.
- Writes `constants.json` as a runtime-friendly object, not a row list.

Expected generated constants shape:

```json
{
  "tick_rate": 20,
  "max_ticks": 1200,
  "board_rows": 3,
  "board_cols": 4,
  "default_seed": 1001
}
```

## Validate config

Validate generated runtime JSON with:

```bash
python tools/validate_config.py --input config/generated
```

Windows Python launcher form:

```bash
py -3.11 tools/validate_config.py --input config/generated
```

The validator currently checks:

- duplicate ids, or duplicate constant keys
- missing required fields
- missing skill, weapon type, unit, and formation references
- negative `hp`, `atk`, `defense`, `range`, `cooldown`, and `attack_interval`
- basic 4x3 formation and encounter coordinate validity
- non-empty `role` values for every formation `pattern.slots` entry
- encounter unit coordinates against the selected formation's `pattern.slots`
- required constants: `tick_rate`, `max_ticks`, `board_rows`, `board_cols`, `default_seed`
- negative numeric constants such as `max_ticks`

With v0.1.3 validation, simulator work can safely rely on `unit coordinate -> formation slot -> role` lookup before applying formation bonuses.

## Load config models

The first Python combat-core layer can load generated JSON into pure config
models without running a battle:

```bash
python tools/inspect_config_models.py --config config/generated
```

Windows Python launcher form:

```bash
py -3.11 tools/inspect_config_models.py --config config/generated
```

Current behavior:

- Reads only `config/generated/*.json`.
- Calls the config validator before loading models.
- Builds a `ConfigBundle` of pure config dataclasses.
- Prints the `demo_001` player and enemy formation coordinate-to-role lookup.
- Acts as the current smoke/debug CLI for the config model layer.

See `docs/process/python-combat-models-v0.1.md` for the model boundary.

`UnitDef / 单位配置定义` is a reusable config definition loaded from runtime JSON. `UnitState / 单位运行时状态` is a per-battle runtime instance created from `UnitDef`, encounter placement / 遭遇战站位, and formation role / 阵型角色. `ConfigBundle / 只读配置集合` is the read-only config collection. `BattleState / 战斗运行时状态` is one battle run's runtime state.

Runtime side enum / 运行时阵营枚举 uses `ally/enemy`.

`config.encounters[].player_units / 配置字段 player_units` enters runtime as `UnitState.side="ally" / 我方阵营`.

`config.encounters[].enemy_units / 配置字段 enemy_units` enters runtime as `UnitState.side="enemy" / 敌方阵营`.

## Run basic combat with skill triggers

After export and validation, run Basic Combat Rules / 基础战斗规则 plus Minimal Skill Triggers / 最小技能触发 with:

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
```

Windows Python launcher form:

```bash
py -3.11 tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
```

Current behavior:

- Loads a `ConfigBundle` from generated runtime JSON.
- Creates `BattleState` and twelve `UnitState` objects for `demo_001`.
- Spawns config `player_units / 玩家单位配置字段` first as `ally_001..ally_006` with runtime side / 运行时阵营 `ally / 我方`.
- Spawns config `enemy_units / 敌方单位配置字段` second as `enemy_001..enemy_006` with runtime side / 运行时阵营 `enemy / 敌方`.
- Emits deterministic `BattleEvent` ids such as `evt_000001`.
- Runs Targeting AI / 目标选择 AI, Basic Attack / 普通攻击, Damage / 伤害, Death / 死亡, and Victory Check / 胜负判断.
- Runs Skill Resolver / 技能解析器, Skill Cooldown / 技能冷却, `on_battle_start / 战斗开始触发`, `on_attack / 攻击时触发`, `on_attacked / 被攻击时触发`, and `on_ally_attacked / 友军被攻击时触发`.
- Emits `skill_trigger event / 技能触发事件`.
- Adds `reason / 伤害原因` to `damage / 伤害` events, using `basic_attack / 普通攻击` or `skill:<skill_id> / 技能 ID`.
- Writes `runs/demo_001/replay.json` with `schema_version="battle_replay.v0.1"` and tick groups containing combat events / 战斗事件.
- Writes `runs/demo_001/debug_timeline.json` as a flat event list.
- Writes `runs/demo_001/battle_report.json` as an event-derived report / 基于事件生成战报 with `damage_done / 输出伤害`, `damage_taken / 承受伤害`, `kills / 击杀`, `skill_triggers / 技能触发次数`, and `key_moments / 关键时刻`.
- Writes `runs/demo_001/run_summary.md` with battle id, seed, unit count, event counts, result, total damage / 总伤害, total kills / 总击杀, total skill triggers / 总技能触发次数, and top unit summaries / 最高单位摘要.
- Ends when one side is eliminated / 一方全灭 or max tick / 最大 tick is reached.

Skeleton compatibility mode / 骨架兼容模式 remains available:

```bash
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode skeleton
```

Current limitations:

No cross-browser Playwright matrix / 无跨浏览器 Playwright 矩阵, no visual regression / 无视觉回归, no C# host / C# 宿主 implementation, no Godot gameplay / 无 Godot 玩法, no xlsx adapter / xlsx 适配器, and no general-purpose Skill DSL / 无通用技能 DSL.

See `docs/process/deterministic-battle-skeleton-v0.1.md` for the runtime skeleton boundary.
See `docs/process/basic-combat-rules-v0.1.md` for Basic Combat Rules / 基础战斗规则.
See `docs/process/minimal-skill-triggers-v0.1.md` for Minimal Skill Triggers / 最小技能触发.
See `docs/process/replay-report-v0.1.md` for Replay Report / 回放与战报.
See `docs/process/svg-replay-viewer-v0.1.md` for SVG Replay Viewer / SVG 回放调试器.

## Run SVG replay viewer

Install the web-viewer dependencies once:

```bash
cd web-viewer
npm install
```

Start the local viewer:

```bash
npm run dev
```

Build and typecheck the viewer:

```bash
npm run build
npm run typecheck
```

Run Browser Smoke Test / 浏览器冒烟测试:

```bash
npx playwright install chromium
npm run test:e2e
```

The Browser Smoke Test / 浏览器冒烟测试 uses Playwright / 浏览器自动化测试工具 with Chromium / Chromium 浏览器. It checks replay/report File Input Loading / 文件输入加载, SVG Board / SVG 棋盘, Timeline / 时间线, Unit Detail Panel / 单位详情面板, Playback Controls / 播放控制, and Report Panel / 战报面板. It is not visual regression / 视觉回归, pixel testing / 像素测试, or a cross-browser matrix / 跨浏览器矩阵.

The viewer reads files through browser file inputs. It does not call a backend and does not run combat logic.

Manual loading targets after a demo run:

```text
runs/demo_001/replay.json
runs/demo_001/battle_report.json
```

The current viewer also supports HTML Demo Complete Experience / HTML 最小 Demo 完整体验闭环 behavior for `demo_001`: Demo Load Guidance / Demo 加载引导, Battle Summary / 战斗摘要, Event Highlight / 事件高亮, Timeline Current Event / 当前事件定位, Report-to-Board Link / 战报到棋盘联动, and Key Moments navigation / 关键时刻跳转. See `docs/process/html-demo-complete-experience-v0.1.md`.

## Battle skeleton module boundary

The v0.1.1 skeleton is split into focused Python modules:

- `runtime_models.py / 运行时模型`: `UnitState`, `BattleState`, `BattleResult`.
- `events.py / 战斗事件`: `BattleEvent`, `event_to_dict`, `events_to_tick_groups`.
- `rng.py / 随机包装器`: `BattleRng`.
- `battle_skeleton.py / 战斗骨架`: `create_battle_state`, `spawn_units_from_encounter`, `run_battle_skeleton`, replay document helpers, and runtime dict serializers.
- `targeting.py / 目标选择`: Targeting AI / 目标选择 AI.
- `combat_rules.py / 战斗规则`: Basic Attack / 普通攻击, Damage / 伤害, and Death / 死亡 helpers.
- `basic_combat.py / 基础战斗`: Basic Combat Rules / 基础战斗规则 runner and Victory Check / 胜负判断.
- `skills.py / 技能解析器`: Minimal Skill Triggers / 最小技能触发, Skill Cooldown / 技能冷却, and `skill_trigger event / 技能触发事件` emission.
- `report.py / 战报生成器`: event-derived report / 基于事件生成战报 for `battle_report.json / 战报 JSON`.
- `battle.py / 兼容转发层`: compatibility facade / 兼容转发层 for old imports. New code should prefer `runtime_models.py`, `events.py`, `rng.py`, `battle_skeleton.py`, `targeting.py`, `combat_rules.py`, `basic_combat.py`, `skills.py`, and `report.py`.

## Test config tools

Run the standard-library unittest suite:

```bash
python -m unittest discover -s sim-python/tests
```

The tests export sample data into a temporary directory and validate both valid and invalid generated config.
They also verify deterministic battle skeleton unit creation, event counts, result payloads, tick grouping, and same-seed event stability.
They verify runtime side enum / 运行时阵营枚举 values `ally/enemy` and keep `battle.py / 兼容转发层` import compatibility covered.
They verify Targeting AI / 目标选择 AI, Basic Attack / 普通攻击, Damage / 伤害, Death / 死亡, Minimal Skill Triggers / 最小技能触发, Skill Cooldown / 技能冷却, Replay Report / 回放与战报, and Basic Combat / 基础战斗 determinism with current in-scope effects, including formation / 阵型 and synergy / 羁绊 modifiers.

## CSV-first note

Designer source format is still intended to be xlsx, and runtime format is still JSON.

Data Config v0.1/v0.1.3 uses CSV sample data first because it gives a dependency-free closed loop for schema, exporter, validator, and tests. This keeps Phase 1 moving without adding an xlsx parser before the data shape is stable.

TODO: add an xlsx adapter behind the same `tools/export_xlsx_to_json.py` command after the schema and validator stabilize.

## Structural verification

Use:

```bash
git status --short
```

Confirm that only intended source files are untracked or changed. Generated files under `config/generated/` are ignored except `.gitkeep`.

## Command flow

The current implemented local simulator flow is:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/inspect_config_models.py --config config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
```

The demo run writes:

- `runs/demo_001/replay.json`
- `runs/demo_001/debug_timeline.json`
- `runs/demo_001/battle_report.json`
- `runs/demo_001/run_summary.md`

Smoke-check the generated Phase 1 MVP artifacts / 第一阶段 MVP 产物:

```bash
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001

Phase 1 demo package one-step flow (minimal):

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
cd web-viewer
npm install
npm run dev
```
```

This smoke check validates replay/report shape and viewer entry files. It does not automate a browser.

## CI workflow local parity / CI 流水线本地对齐

主干门禁（Main Gate / 主干门禁）采用 PR 和 `main` push 触发。对应文档：

- `docs/process/ci-workflow-v0.1.md`

本地可先按 CI 对齐运行：

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
python -m unittest discover -s sim-python/tests

cd web-viewer
npm install
npm run typecheck
npm run build
npx playwright install chromium --with-deps
npm run test:e2e
```

当前 CI 对齐命令使用 `npm install`。`npm ci` 在 Windows/Linux 可选依赖锁文件噪音（optional dependency lockfile churn）场景下不稳定，故暂时下沉为后续任务的理想目标。

Phase 1 review docs:

- `docs/process/phase-1-mvp-review.md`
- `docs/process/viewer-smoke-checklist.md`
- `docs/process/viewer-browser-smoke-v0.1.md`
- `docs/process/html-demo-complete-experience-v0.1.md`

C# host commands are still future work.
