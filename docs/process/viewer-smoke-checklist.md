# Viewer Smoke Checklist / 回放器冒烟清单

This checklist is a Manual Smoke / 手动冒烟 checklist for the SVG Replay Viewer / SVG 回放调试器.

It intentionally does not use Playwright / 浏览器自动化 or add browser-test dependencies / 浏览器测试依赖.

For automated Browser Smoke Test / 浏览器冒烟测试 coverage, see `docs/process/viewer-browser-smoke-v0.1.md`.

For HTML Demo Complete Experience / HTML 最小 Demo 完整体验闭环 behavior, see `docs/process/html-demo-complete-experience-v0.1.md`.

## Prerequisites / 前置条件

Generate demo artifacts / 生成演示产物:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
```

Start the viewer / 启动回放器:

```bash
cd web-viewer
npm install
npm run dev
```

Open the local URL printed by Vite / 打开 Vite 输出的本地地址, usually:

```text
http://127.0.0.1:5173/
```

## Load Files / 加载文件

Load these two files through browser file inputs / 通过浏览器文件输入加载以下两个文件:

- `runs/demo_001/replay.json`
- `runs/demo_001/battle_report.json`

Expected / 预期:

- status line / 状态行 shows both files loaded.
- metadata / 元数据显示 `demo_001`, seed `1001`, and event count.
- Demo Load Guidance / Demo 加载引导 shows the generation commands and expected files.
- Battle Summary / 战斗摘要 shows winner / 胜者, reason / 原因, end_tick / 结束 tick, total_damage / 总伤害, total_kills / 总击杀, and total_skill_triggers / 总技能触发次数.
- no backend request / 无后端请求 is needed.

## Board Checks / 棋盘检查

Confirm / 确认:

- SVG Board / SVG 棋盘 shows Ally / 我方 and Enemy / 敌方 sides.
- There are 12 units / 12 个单位.
- Unit tokens / 单位标记 show instance id / 实例 ID, role / 阵型角色, and HP / 血量.
- Dead units / 死亡单位 become visually distinct after seeking past death events.
- Latest attack / 最近攻击, skill / 技能, and damage / 伤害 markers appear while seeking.

## Timeline Checks / 时间线检查

Confirm / 确认:

- Timeline / 时间线 lists replay events / 回放事件.
- Event filters / 事件过滤 work for:
  - all / 全部
  - attack / 攻击
  - skill_trigger / 技能触发
  - damage / 伤害
  - death / 死亡
  - battle_end / 战斗结束
- Clicking an event / 点击事件 seeks to that tick / 跳转到该 tick.
- The selected event row / 选中事件行 stays visibly highlighted and scrolls into view.

## Event Highlight Checks / 事件高亮检查

Confirm / 确认:

- Event Highlight / 事件高亮 shows the current event id / 当前事件 ID, type / 类型, tick / tick, and summary / 摘要.
- `skill_trigger / 技能触发` highlights source / 来源 and targets / 目标 on the SVG Board / SVG 棋盘.
- `damage / 伤害` highlights the target / 目标 and shows reason / 伤害原因.
- `death / 死亡` makes the dead unit / 死亡单位 visually stronger.
- `battle_end / 战斗结束` shows the final winner / 胜者 and reason / 原因.

## Playback Checks / 播放检查

Confirm / 确认:

- Play / 播放 advances by discrete ticks / 离散 tick.
- Pause / 暂停 stops playback.
- Step Tick / 单 tick 前进 increments tick by 1.
- Previous Event / 上一个事件 and Next Event / 下一个事件 move between event positions.
- Tick slider / tick 滑条 seeks to the selected tick.
- Speed select / 速度选择 changes playback tick rate.
- Current event id / 当前事件 ID is visible.
- Current tick / 当前 tick and max tick / 最大 tick are visible.
- Play / 播放 stops at battle_end / 战斗结束. Pressing Play from or past the end tick restarts from tick 0.

## Report Checks / 战报检查

Confirm / 确认:

- Battle Report / 战报 shows winner / 胜者, reason / 原因, and end_tick / 结束 tick.
- Summary / 汇总 shows total_damage / 总伤害, total_kills / 总击杀, and total_skill_triggers / 总技能触发次数.
- Top Units / 最高单位 lists damage_done / 输出伤害, damage_taken / 承受伤害, and skill_triggers / 技能触发次数.
- Unit Reports / 单位战报 table shows per-unit stats / 单位统计.
- Key Moments / 关键时刻 includes death / 死亡 and battle_end / 战斗结束 entries.
- Clicking a unit id / 点击单位 ID in Unit Reports / 单位战报 or Top Units / 最高单位 selects that board unit / 棋盘单位.
- Clicking a Key Moment / 关键时刻 seeks to its tick / 跳转到对应 tick.

## Unit Detail Checks / 单位详情检查

Confirm / 确认:

- Clicking a unit / 点击单位 updates Unit Detail Panel / 单位详情面板.
- Unit Detail Panel / 单位详情面板 shows side / 阵营, role / 角色, position / 坐标, HP / 血量, alive state / 存活状态, and report stats / 战报统计.
- Selecting a dead unit / 选择死亡单位 still shows its final report stats / 最终战报统计.

## Pass Record / 通过记录

Use this template in PR notes / 在 PR 记录中使用此模板:

```text
Viewer Smoke / 回放器冒烟:
- replay loaded: yes/no
- report loaded: yes/no
- board shows 12 units: yes/no
- timeline filters work: yes/no
- playback controls work: yes/no
- report panel matches battle_report.json: yes/no
- report-to-board link works: yes/no
- key moments seek tick: yes/no
- event highlight shows current event: yes/no
- unit detail updates on click: yes/no
- no backend required: yes/no
```

## Known Manual Limit / 已知手动限制

This checklist is not an Automated Browser Test / 自动浏览器测试. It is a repeatable manual smoke surface / 可重复手动冒烟面 for Phase 1 MVP Review / 第一阶段 MVP 复盘.

The Playwright / 浏览器自动化测试工具 version of this smoke is intentionally minimal: it verifies File Input Loading / 文件输入加载 and the current Viewer Contract / 回放器契约, but it does not perform visual regression / 视觉回归 or pixel checks / 像素检查.
