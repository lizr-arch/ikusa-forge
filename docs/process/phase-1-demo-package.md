# Phase 1 Demo Package / 第一阶段演示包

## Purpose / 目的

这是用于演示当前 Phase 1 MVP 的可交付说明。目标是给评审、演示、验收提供一套一致的运行和检查入口；Demo One-Click / 一键 Demo 只扩展静态样例加载入口，不新增战斗系统功能，不改战斗规则。

## What This Demo Shows / 这个 Demo 展示什么

本演示包验证并展示以下能力：

- Config Pipeline / 配置流水线
- Deterministic Battle / 确定性战斗
- Basic Combat / 基础战斗
- Minimal Skill Triggers / 最小技能触发
- Replay Events / 回放事件
- Battle Report / 战报
- SVG Replay Viewer / SVG 回放调试器
- Combat System Pack / 战斗系统包 explainability: status lifecycle / 状态生命周期, skill cooldown / 技能冷却, action timeline / 行动时间线, victory explanation / 胜负解释
- Demo One-Click / 一键 Demo and Scenario Selector / 场景选择器 powered by Scenario Manifest / 场景清单
- Live Combat Runtime / 实时战斗运行时 compatibility: `run_basic_combat` still generates the same replay/report while BattleSession / 战斗会话 can be stepped in tests.
- Browser Smoke / 浏览器冒烟测试

## Demo Prerequisites / 演示前置条件

在开始前确认：

- Python >= 3.10（推荐 3.11+）
- Node.js + npm
- Playwright Chromium browser（自动冒烟依赖）
- repo 已 clone 并在 `main` 分支下完成最新 pull

## Demo Setup Commands / 演示准备命令

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003
python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples
python -m unittest discover -s sim-python/tests

cd web-viewer
npm install
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
npm run dev -- --host 127.0.0.1
```

## Viewer Demo Steps / 回放器演示步骤

1. 打开 `http://127.0.0.1:5173`
2. 查看 Scenario Selector / 场景选择器
3. 点击 Load Baseline Demo / 加载默认 Demo，直接加载 Curated Fixture / 固化样例数据
4. 确认 Scenario Summary / 场景摘要 显示 `demo_001`
5. 查看 Battle Summary / 战斗摘要
6. 点击 Play / 播放
7. 使用 Next Event / Previous Event
8. 使用 Timeline Filter / 时间线筛选 `damage`、`skill_trigger`、`death`、`status_apply`、`skill_cooldown`、`action_scheduled`
9. 点击 `ally_001` 查看 Unit Detail / 单位详情，并查看 Active Statuses / 当前状态 与 Next Action Tick / 下一行动 tick
10. 点击 Report Panel / 战报面板 中的 top unit 观察棋盘联动
11. 点击 Key Moment / 关键时刻 跳到 `battle_end`
12. 解释 `winner=ally`, `reason=enemy_eliminated`, `winner_alive=3`, `winner_total_hp=286`

Manual File Input Loading / 手动文件输入加载 remains available for locally generated files:

```text
runs/demo_001/replay.json
runs/demo_001/battle_report.json
```

## Expected Demo Result / 预期演示结果

在当前主线下，`demo_001` 预期结果如下：

- units / 单位数: `12`
- events / 事件数: `332`
- winner / 胜者: `ally`
- reason / 原因: `enemy_eliminated`
- end_tick / 结束 tick: `240`
- total_damage / 总伤害: `1189`
- total_kills / 总击杀: `9`
- total_skill_triggers / 总技能触发: `48`
- total_modifiers / 总修正次数: `16`
- formation_modifiers / 阵型加成次数: `8`
- synergy_modifiers / 羁绊加成次数: `8`
- total_status_applied / 总状态应用次数: `4`
- total_status_expired / 总状态过期次数: `0`
- total_skill_cooldowns / 总技能冷却次数: `48`
- total_actions_scheduled / 总行动排期次数: `75`
- winner_alive / 胜者存活数: `3`
- loser_alive / 败者存活数: `0`
- winner_total_hp / 胜者剩余总 HP: `286`
- loser_total_hp / 败者剩余总 HP: `0`
- curated scenario count / 固化场景数量: `3`
- scenario ids / 场景 ID: `demo_001`, `demo_seed_1002`, `demo_seed_1003`

### Supported Synergy Stats / 支持的羁绊属性

- `hp`
- `attack_interval_delta`

### Unsupported (for this phase) / 本阶段不支持

- `opening_damage`（未在 current 战斗流程中映射为事件修正源）
- `formation_slots`（当前统计未覆盖该维度）

当前 `demo_001` 验证要求：

- `battle_report.json` `summary.total_modifiers > 0`
- `battle_report.json` `summary.formation_modifiers > 0`
- `battle_report.json` `summary.synergy_modifiers > 0`
- `debug_timeline.json` 存在 `stat_modifier` 且 `source_type` 同时出现 `formation` 与 `synergy`
- `debug_timeline.json` 存在 `status_apply`、`skill_cooldown`、`action_scheduled`
- `battle_report.json` 存在 `victory_explanation`

如果这些值未来因为规则调整变化，请同步更新本页、`tools/smoke_phase1_mvp.py`，以及本阶段 smoke 覆盖说明。

## Demo Narrative / 演示叙事

- 我们先从配置生成运行时数据（`config/source -> config/generated`）。
- 通过固定参数运行 Python simulator 进行 demo，保证确定性（`seed=1001`）。
- `replay.json` 记录事件流，`battle_report.json` 归纳伤害、击杀和触发。
- Combat System Pack / 战斗系统包新增事件只解释状态、冷却、行动排期与胜负摘要，不改变战斗公式。
- Demo One-Click / 一键 Demo 通过 Scenario Manifest / 场景清单 加载静态 replay/report，不需要后端。
- Live Combat Runtime Foundation / 实时战斗运行时基础 把一次性战斗循环封装成 BattleSession / 战斗会话、Step Runtime / 单步运行时、Battle Snapshot / 战斗状态快照 和 Event Buffer / 事件缓冲，但 demo 仍通过同一个 `run_basic_combat` 入口生成 replay/report。
- Web viewer 只读取回放文件，不运行战斗逻辑。
- 通过 board / timeline / report / unit detail 逐步回看一场战斗闭环。
- 浏览器冒烟测试保证关键体验通路有最小自动化保障。

## Acceptance Checklist / 验收清单

- [ ] config export passed / 配置导出通过
- [ ] config validation passed / 配置校验通过
- [ ] demo battle generated / 演示战斗已生成
- [ ] static MVP smoke passed / MVP 静态冒烟通过
- [ ] scenario smoke passed / 场景冒烟通过
- [ ] Python unittest passed / Python 单测通过
- [ ] BattleSession tests passed / 战斗会话测试通过
- [ ] web typecheck passed / 前端类型检查通过
- [ ] web build passed / 前端构建通过
- [ ] browser smoke passed / 浏览器冒烟通过
- [ ] viewer loads replay/report / 回放器成功加载 replay 与 report
- [ ] viewer loads curated scenario without manual file input / 回放器无需手动文件输入即可加载固化场景
- [ ] manual file input still works / 手动文件输入仍可用
- [ ] board shows 12 units / 棋盘显示 12 个单位
- [ ] battle summary shows ally / enemy_eliminated / 战斗摘要显示 ally / enemy_eliminated
- [ ] timeline filter works / 时间线筛选可用
- [ ] combat-system timeline filters work / 战斗系统事件筛选可用
- [ ] unit detail shows active status and next action / 单位详情显示当前状态和下一行动
- [ ] report shows victory explanation / 战报显示胜负解释
- [ ] report-to-board link works / 战报到棋盘联动可用
- [ ] key moments navigation works / 关键时刻跳转可用

## Known Limits / 已知限制

- 离散 tick/event 播放，不是平滑动画
- 无视觉回归
- 无跨浏览器矩阵
- 无 HTTP server / HTTP 服务器
- 无 HTML live mode / HTML 实时模式
- 无 C# host / C# 宿主
- 无 Godot
- xlsx adapter / xlsx 适配器
- 当前不是完整游戏，只是战斗实验室 / not a full game, only a combat lab

## Next Direction Options / 下一阶段方向选项

下一步方向优先级建议（含简短对比）：

1. Combat Behavior Pack / 战斗行为包
   目标是目标选择与技能选择可解释：记录 `target_reason`、`target_score`，并把决策原因在战报与回放器里可见。
2. Viewer polish / 回放器打磨
   目标是提升可展示性、联动体验和讲述清晰度；最小风险，最短交付。
3. CI workflow / CI 流水线
   目标是把当前 Python + Web 验证命令收敛为提交门禁；涉及工程自动化，收益中等。
4. Formation bonus / 阵型加成
   目标是补齐策略深度；会带来玩法行为改变，需要新增校验和回归评估。
5. Synergy application / 羁绊应用
   目标是增强单位关系策略；与阵型加成同为核心玩法改动，需先收敛报告与冒烟。
6. C# host / C# 宿主
   目标是完成跨语言调用链；属于工程边界推进，不改变战斗公式。
7. Godot shell / Godot 外壳
   目标是外壳与演示入口；会暴露当前展示层缺口，适合作为阶段末目标。
8. xlsx adapter / xlsx 适配器
   目标是直接运行 xlsx 输入；目前仍不在 Phase 1 主线范围。

优先建议：Phase 1 演示包交付后，优先做 `CI workflow / CI 流水线` 或 `Viewer polish / 回放器打磨`。若目标是玩法深度，再进入 `formation bonus / 阵型加成` 与 `synergy / 羁绊应用`。
