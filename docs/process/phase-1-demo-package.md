# Phase 1 Demo Package / 第一阶段演示包

## Purpose / 目的

这是用于演示当前 Phase 1 MVP 的可交付说明。目标是给评审、演示、验收提供一套一致的运行和检查入口，不新增系统功能，不改战斗规则，不扩展回放器能力。

## What This Demo Shows / 这个 Demo 展示什么

本演示包验证并展示以下能力：

- Config Pipeline / 配置流水线
- Deterministic Battle / 确定性战斗
- Basic Combat / 基础战斗
- Minimal Skill Triggers / 最小技能触发
- Replay Events / 回放事件
- Battle Report / 战报
- SVG Replay Viewer / SVG 回放调试器
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
2. 在页面查看 Demo Load Guidance / Demo 加载引导
3. 加载 `runs/demo_001/replay.json`
4. 加载 `runs/demo_001/battle_report.json`
5. 查看 Battle Summary / 战斗摘要
6. 点击 Play / 播放
7. 使用 Next Event / Previous Event
8. 使用 Timeline Filter / 时间线筛选 `damage`、`skill_trigger`、`death`
9. 点击 `ally_001` 查看 Unit Detail / 单位详情
10. 点击 Report Panel / 战报面板 中的 top unit 观察棋盘联动
11. 点击 Key Moment / 关键时刻 跳到 `battle_end`
12. 解释 `winner=ally`, `reason=enemy_eliminated`

## Expected Demo Result / 预期演示结果

在当前主线下，`demo_001` 预期结果如下：

- units / 单位数: `12`
- events / 事件数: `217`
- winner / 胜者: `ally`
- reason / 原因: `enemy_eliminated`
- end_tick / 结束 tick: `260`
- total_damage / 总伤害: `1219`
- total_kills / 总击杀: `9`
- total_skill_triggers / 总技能触发: `54`

如果这些值未来因为规则调整变化，请同步更新本页、`tools/smoke_phase1_mvp.py`，以及本阶段 smoke 覆盖说明。

## Demo Narrative / 演示叙事

- 我们先从配置生成运行时数据（`config/source -> config/generated`）。
- 通过固定参数运行 Python simulator 进行 demo，保证确定性（`seed=1001`）。
- `replay.json` 记录事件流，`battle_report.json` 归纳伤害、击杀和触发。
- Web viewer 只读取回放文件，不运行战斗逻辑。
- 通过 board / timeline / report / unit detail 逐步回看一场战斗闭环。
- 浏览器冒烟测试保证关键体验通路有最小自动化保障。

## Acceptance Checklist / 验收清单

- [ ] config export passed / 配置导出通过
- [ ] config validation passed / 配置校验通过
- [ ] demo battle generated / 演示战斗已生成
- [ ] static MVP smoke passed / MVP 静态冒烟通过
- [ ] Python unittest passed / Python 单测通过
- [ ] web typecheck passed / 前端类型检查通过
- [ ] web build passed / 前端构建通过
- [ ] browser smoke passed / 浏览器冒烟通过
- [ ] viewer loads replay/report / 回放器成功加载 replay 与 report
- [ ] board shows 12 units / 棋盘显示 12 个单位
- [ ] battle summary shows ally / enemy_eliminated / 战斗摘要显示 ally / enemy_eliminated
- [ ] timeline filter works / 时间线筛选可用
- [ ] report-to-board link works / 战报到棋盘联动可用
- [ ] key moments navigation works / 关键时刻跳转可用

## Known Limits / 已知限制

- 离散 tick/event 播放，不是平滑动画
- 无视觉回归
- 无跨浏览器矩阵
- 无 C# host / C# 宿主
- 无 Godot
- 无羁绊（synergy）
- 无阵型加成（formation bonus）
- 无 xlsx adapter / xlsx 适配器
- 当前不是完整游戏，只是 combat lab / 当前不是完整游戏，只是战斗实验室

## Next Direction Options / 下一阶段方向选项

下一步方向优先级建议（含简短对比）：

1. Viewer polish / 回放器打磨  
   目标是提升可展示性、联动体验和讲述清晰度；最小风险，最短交付。
2. CI workflow / CI 流水线  
   目标是把当前 Python + Web 验证命令收敛为提交门禁；涉及工程自动化，收益中等。
3. Formation bonus / 阵型加成  
   目标是补齐策略深度；会带来玩法行为改变，需要新增校验和回归评估。
4. Synergy application / 羁绊应用  
   目标是增强单位关系策略；与阵型加成同为核心玩法改动，需先收敛报告与冒烟。
5. C# host / C# 宿主  
   目标是完成跨语言调用链；属于工程边界推进，不改变战斗公式。
6. Godot shell / Godot 外壳  
   目标是外壳与演示入口；会暴露当前展示层缺口，适合作为阶段末目标。
7. xlsx adapter / xlsx 适配器  
   目标是直接运行 xlsx 输入；目前仍不在 Phase 1 主线范围。

优先建议：Phase 1 演示包交付后，优先做 `CI workflow / CI 流水线` 或 `Viewer polish / 回放器打磨`。若目标是玩法深度，再进入 `formation bonus / 阵型加成` 与 `synergy / 羁绊应用`。
