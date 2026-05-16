# Phase 1 MVP Review / 第一阶段 MVP 复盘

This document records the Phase 1 MVP Review / 第一阶段 MVP 复盘 after the SVG Replay Viewer / SVG 回放调试器 landed on `main`.

The purpose is not to add a new system. The purpose is to verify the current closed loop, name the remaining gaps, and decide what should be reviewed before the next implementation branch.

## Scope / 范围

Included in this review:

- Demo Run Checklist / 演示运行清单.
- Combat Findings / 战斗观察.
- Report Findings / 战报观察.
- Viewer Findings / 回放器观察.
- Blocking Issues / 阻塞问题.
- Next Direction Decision / 下一步方向决策.

Not included in this review:

- New combat rules / 新战斗规则.
- New skill effects / 新技能效果.
- Synergy application / 羁绊应用.
- Formation bonus application / 阵型加成应用.
- C# host / C# 宿主.
- Godot.
- xlsx adapter / xlsx 适配器.
- React / Vue / Phaser / PixiJS / Three.js.
- Backend server / 后端服务.

## Current MVP Capability / 当前 MVP 能力

Current `main` has a closed Phase 1 validation loop:

- config pipeline / 配置流水线: CSV sample data is exported through the stable `tools/export_xlsx_to_json.py` command into runtime JSON / 运行时 JSON.
- deterministic simulator / 确定性模拟器: Same config / 配置, battle setup / 战斗设置, and seed / 随机种子 produce the same replay/report output.
- basic combat / 基础战斗: Targeting AI / 目标选择 AI, Basic Attack / 普通攻击, Damage / 伤害, Death / 死亡, and Victory Check / 胜负判断 run in `--mode basic`.
- skill triggers / 技能触发: Minimal Skill Triggers / 最小技能触发 cover fixed sample handlers, cooldowns, damage reasons, guard, rally, counters, and intercepts.
- replay events / 回放事件: `battle_start`, `unit_spawn`, `attack`, `skill_trigger`, `damage`, `death`, and `battle_end` are serialized into tick groups.
- battle_report.json / 战报 JSON: The report summarizes total damage / 总伤害, kills / 击杀, skill triggers / 技能触发次数, top units / 最高单位, and key moments / 关键时刻.
- SVG replay viewer / SVG 回放调试器: The Vite + TypeScript viewer loads local replay/report files, reconstructs Visual State / 可视化状态, and renders board, timeline, playback controls, report, and unit detail without backend calls.

## Demo Run Checklist / 演示运行清单

From a clean checkout / 干净检出, generate current demo artifacts / 演示产物:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
```

Run tests / 运行测试:

```bash
python -m unittest discover -s sim-python/tests
```

Start the SVG Replay Viewer / SVG 回放调试器:

```bash
cd web-viewer
npm install
npm run dev
```

Load these files manually / 手动加载这些文件:

```text
runs/demo_001/replay.json
runs/demo_001/battle_report.json
```

Verify frontend build checks / 验证前端构建检查:

```bash
cd web-viewer
npm run typecheck
npm run build
```

Generated artifacts / 生成产物 are ignored and should not be committed:

- `config/generated/*.json`
- `runs/demo_001/replay.json`
- `runs/demo_001/debug_timeline.json`
- `runs/demo_001/battle_report.json`
- `runs/demo_001/run_summary.md`
- `web-viewer/dist/`
- `web-viewer/node_modules/`

## Current Demo Snapshot / 当前演示快照

The current `demo_001` basic run with seed `1001` produced:

| Metric / 指标 | Value / 数值 |
|---|---:|
| unit_count / 单位数量 | 12 |
| events / 事件总数 | 217 |
| result / 结果 | ally / enemy_eliminated |
| end_tick / 结束 tick | 260 |
| skill_trigger events / 技能触发事件 | 54 |
| attack events / 攻击事件 | 45 |
| damage events / 伤害事件 | 95 |
| death events / 死亡事件 | 9 |
| total_damage / 总伤害 | 1219 |
| total_kills / 总击杀 | 9 |
| total_skill_triggers / 总技能触发次数 | 54 |

Top report units / 战报最高单位:

- damage_done / 输出伤害: `ally_004`, `ally_003`, `enemy_003`.
- damage_taken / 承受伤害: `enemy_001`, `ally_001`, `enemy_002`.
- skill_triggers / 技能触发次数: `ally_003`, `enemy_003`, `ally_005`.

## Combat Findings / 战斗观察

Confirmed:

- The simulator has a complete deterministic combat loop / 确定性战斗循环 for the sample encounter.
- Targeting AI / 目标选择 AI and Basic Attack / 普通攻击 produce visible unit deaths and a final winner.
- Skill Resolver / 技能解析器 changes the damage profile through skill-triggered damage and defensive/reaction effects.
- The battle ends by Victory Check / 胜负判断, not by timeout, for `demo_001`.

Still limited:

- Synergy application / 羁绊应用 is data-shaped but not applied in combat.
- Formation bonus application / 阵型加成应用 is data-shaped but not applied in combat.
- Skills are MVP fixed handlers / MVP 固定处理器, not a general-purpose Skill DSL / 通用技能 DSL.
- Balance is demonstrative / 演示性质, not final production balance / 最终生产平衡.

## Report Findings / 战报观察

Confirmed:

- `battle_report.json / 战报 JSON` is derived from replay events / 回放事件.
- Summary / 汇总, Unit Report / 单位战报, Top Units / 最高单位, and Key Moments / 关键时刻 are present.
- Kill Attribution / 击杀归因 uses last damage source / 最近伤害来源 and is visible in key moments.
- `run_summary.md / 运行摘要` gives a compact text summary for demos and PR reports.

Still limited:

- The report is battle-output focused / 战斗输出导向; it does not yet explain formation contribution / 阵型贡献 or synergy contribution / 羁绊贡献.
- The report does not yet include designer-facing delta comparisons / 面向策划的差异对比 between runs.

## Viewer Findings / 回放器观察

Confirmed:

- The SVG Replay Viewer / SVG 回放调试器 is read-only and loads local files through browser file inputs.
- Visual State / 可视化状态 is reconstructed from replay events instead of simulator internals.
- SVG Board / SVG 棋盘 shows both sides' 4x3 grids, units, HP, role, alive/dead state, and latest attack/skill/damage markers.
- Timeline / 时间线 can filter event types and seek to events.
- Report Panel / 战报面板 and Unit Detail Panel / 单位详情面板 make the generated report inspectable.

Still limited:

- No automated browser test / 自动浏览器测试 yet.
- Playback is discrete tick/event navigation / 离散 tick 或事件跳转, not smooth animation / 平滑动画.
- Viewer smoke is currently a Manual Smoke / 手动冒烟 checklist plus static artifact smoke script / 静态产物冒烟脚本.

## Blocking Issues / 阻塞问题

These are the current blockers for a playable or public demo / 可玩或公开演示:

1. C# host / C# 宿主 is still missing, so non-Python users do not have a stable launcher.
2. Godot shell / Godot 外壳 is still missing, so there is no game-like presentation or input surface.
3. Viewer polish / 回放器打磨 is enough for debugging, but not yet enough for a polished public showcase.
4. Synergy application / 羁绊应用 and Formation bonus application / 阵型加成应用 are not applied, so formation/identity strategy is not yet fully represented.
5. xlsx adapter / xlsx 适配器 is not implemented, so designer editing still uses CSV sample data behind the stable exporter command.

## Next Direction Decision / 下一步方向决策

Recommendation / 建议:

Do not immediately add another major system. First run a short review branch or checklist session around the current MVP:

```text
phase1/mvp-review-and-hardening
```

Decision options / 决策选项 after this review:

| Option / 选项 | When it is best / 适用条件 | Main risk / 主要风险 |
|---|---|---|
| C# host / C# 宿主 | Choose this if the priority is a stable non-Python command entry. | It improves operation, but not player-facing feel. |
| Godot shell / Godot 外壳 | Choose this if the priority is playable presentation. | It may expose missing UX and content gaps quickly. |
| Viewer polish / 回放器打磨 | Choose this if the priority is explainability and demo review. | It can delay actual host/game integration. |
| synergy/formation bonuses / 羁绊和阵型加成 | Choose this if the priority is strategy depth. | It changes combat behavior and needs stronger balance/test coverage. |

Current preference / 当前倾向:

Use the current viewer to review one demo manually, then choose between C# host / C# 宿主 and Viewer polish / 回放器打磨 before adding synergy/formation bonuses / 羁绊和阵型加成. This keeps the next step operational and evidence-based.

## Verification Evidence / 验证证据

Baseline commands run for this review:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python -m unittest discover -s sim-python/tests
cd web-viewer
npm install
npm run typecheck
npm run build
```

Observed outputs / 观察到的输出:

- exporter / 导出器: exported 7 config tables.
- validator / 校验器: config validation passed.
- demo run / 演示运行: 12 units, 217 events, ally / enemy_eliminated.
- unittest / 单元测试: 65 tests passed.
- npm install / 前端依赖安装: 0 vulnerabilities.
- typecheck / 类型检查: `tsc --noEmit` passed.
- build / 构建: Vite build passed.

## Review Rule Answers / 评审规则回答

1. What player/combat behavior changed? / 玩家或战斗行为改变了什么？
   - None / 无. This is review and hardening only.
2. What data changed? / 数据改变了什么？
   - None / 无 runtime data. Generated demo artifacts were produced locally and ignored.
3. What replay/report proves it? / 哪些回放或战报证明它？
   - `runs/demo_001/replay.json` and `runs/demo_001/battle_report.json` from the smoke run prove the current MVP still closes.
4. What tests protect it? / 哪些测试保护它？
   - Python unittest suite / Python 单元测试, Web typecheck/build / 前端类型检查和构建, and `tools/smoke_phase1_mvp.py`.
5. What is still uncertain? / 仍然不确定什么？
   - Manual viewer UX / 手动回放器体验, public demo readiness / 公开演示就绪度, and next system priority / 下一系统优先级.
