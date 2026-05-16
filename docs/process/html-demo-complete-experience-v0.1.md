# HTML Demo Complete Experience / HTML 最小 Demo 完整体验闭环 v0.1

This stage improves the HTML Demo Complete Experience / HTML 最小 Demo 完整体验闭环 for the existing SVG Replay Viewer / SVG 回放调试器.

It does not add combat rules / 战斗规则. It makes the current `demo_001` replay/report easier to generate, load, inspect, and smoke-test inside the HTML viewer.

## Goal / 目标

The goal is to let a reviewer run one complete demo battle / 完整演示战斗 and inspect the result end to end:

- generate `replay.json / 回放 JSON` and `battle_report.json / 战报 JSON`;
- load both files through browser File Input Loading / 文件输入加载;
- read the Battle Summary / 战斗摘要 immediately;
- inspect Event Highlight / 事件高亮 on the SVG Board / SVG 棋盘 and Timeline / 时间线;
- click report units through Report-to-Board Link / 战报到棋盘联动;
- jump from Key Moments / 关键时刻 to the relevant tick.

## Demo Flow / Demo 流程

Generate config and demo artifacts / 生成配置与演示产物:

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

Load these files manually / 手动加载这些文件:

```text
runs/demo_001/replay.json
runs/demo_001/battle_report.json
```

The viewer shows Demo Load Guidance / Demo 加载引导 because browsers cannot read arbitrary local paths automatically. The existing file inputs remain the source of truth / 事实来源 for local replay/report loading.

## Viewer Behavior / 回放器行为

Battle Summary / 战斗摘要 shows the loaded battle id / 战斗 ID, seed / 随机种子, winner / 胜者, reason / 原因, end tick / 结束 tick, event count / 事件数量, total damage / 总伤害, total kills / 总击杀, and skill trigger count / 技能触发次数.

Event Highlight / 事件高亮 shows the current event id / 当前事件 ID, event type / 事件类型, tick / tick, summary / 摘要, and event-specific details:

- skill_trigger / 技能触发: source / 来源, skill / 技能, trigger / 触发器, targets / 目标.
- damage / 伤害: source / 来源, target / 目标, amount / 数值, reason / 原因.
- death / 死亡: dead unit / 死亡单位.
- battle_end / 战斗结束: winner / 胜者, reason / 原因, end tick / 结束 tick.

SVG Board / SVG 棋盘 highlights current event participants / 当前事件参与单位 with simple SVG rings and CSS classes. It keeps playback discrete / 离散: tick/event navigation only, not smooth animation / 平滑动画.

Timeline Current Event / 当前事件定位 highlights the selected event row / 选中事件行 and keeps it visible with `scrollIntoView`.

Report-to-Board Link / 战报到棋盘联动 is available from Report Panel / 战报面板 unit rows and top-unit entries: clicking a unit id selects the board unit and updates Unit Detail Panel / 单位详情面板.

Key Moments navigation / 关键时刻跳转 lets death / 死亡 and battle_end / 战斗结束 moments seek to their tick.

Playback Controls / 播放控制 show the current tick / 当前 tick, max tick / 最大 tick, and current event id / 当前事件 ID. Play stops at `battle_end / 战斗结束`; pressing Play from or past the end tick restarts from tick 0.

## Test Coverage / 测试覆盖

The End-to-End Demo Smoke / 端到端 Demo 冒烟 remains intentionally small. `web-viewer/tests/viewer-smoke.spec.ts` verifies:

- Page Load / 页面加载.
- File Input Loading / 文件输入加载 for replay/report.
- Demo Load Guidance / Demo 加载引导.
- Battle Summary / 战斗摘要 values.
- Board View / 棋盘视图 and 12 unit tokens / 单位标记.
- Timeline / 时间线 filters and selected row / 选中行.
- Event Highlight / 事件高亮 summary and damage reason / 伤害原因.
- Unit Detail Panel / 单位详情面板.
- Playback Controls / 播放控制.
- Report-to-Board Link / 战报到棋盘联动.
- Key Moments navigation / 关键时刻跳转.
- Report Panel / 战报面板.

Run it with:

```bash
cd web-viewer
npm run test:e2e
```

## Not in Scope / 不在范围

This stage does not include:

- new combat rules / 新战斗规则;
- new skill effects / 新技能效果;
- synergy application / 羁绊应用;
- formation bonus application / 阵型加成应用;
- C# host / C# 宿主;
- Godot;
- xlsx adapter / xlsx 适配器;
- backend server / 后端服务;
- React / Vue / Phaser / PixiJS / Three.js;
- complex animation system / 复杂动画系统;
- visual regression / 视觉回归;
- screenshot baseline / 截图基准测试;
- cross-browser matrix / 跨浏览器矩阵.

Generated artifacts / 生成产物 such as `config/generated/`, `runs/demo_001/`, `web-viewer/dist/`, and browser test outputs remain local and should not be committed.
