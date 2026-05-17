# Phase 1 Summary / 第一阶段总结

## Phase 1 Completed Capabilities / 第一阶段已完成能力

- Deterministic pipeline from config / 配置到输出的确定性链路
- Python deterministic simulator / Python 确定性模拟器（`basic` 模式）
- Replay and report output / 回放与战报输出
- SVG Replay Viewer / SVG 回放调试器（read-only 本地回放查看）
- Formation bonus / 阵型加成（推荐规则）与 Synergy application / 羁绊应用（推荐规则）在 tick 0 一次性应用并可追踪
- Targeting explainability / 目标选择可解释性（`target_reason` / `target_score`）初步链路
- Browser Smoke Test / 浏览器冒烟测试（Playwright 基础检查）
- Verified real `demo_001` modifier evidence：
  - formation modifiers in report summary / 战报阵型修正数 > 0
  - synergy modifiers in report summary / 战报羁绊修正数 > 0
  - `stat_modifier` events with both `source_type=formation` and `source_type=synergy`

## Major PRs / 主要 PR

- #1 `feat(config): add phase 1 data config pipeline`
- #2 `feat(sim): add config loader and combat models`
- #3 `feat(sim): add deterministic battle skeleton`
- #4 `feat(sim): add basic combat rules`
- #5 `feat(sim): add minimal skill triggers`
- #6 `feat(sim): add replay battle report`
- #7 `feat(viewer): add svg replay viewer`
- #8 `docs(process): add phase 1 mvp review`
- #9 `test(viewer): add browser smoke test`
- #10 `feat(viewer): improve html demo experience`
- #11 `docs(process): add phase 1 demo package` (current / pending review)
- #12 `feat(sim): add tactical depth pack` (current / pending review)
- #13 `ci: add phase 2 validation workflow` (current / pending review)

## Current Commands / 当前命令

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
npm run test:e2e
```

## Current Artifacts / 当前产物

可复用演示产物（本地生成，不提交）：

- `runs/demo_001/replay.json`
- `runs/demo_001/battle_report.json`
- `runs/demo_001/debug_timeline.json`
- `runs/demo_001/run_summary.md`
- `web-viewer/dist/`（前端产物）

## Known Limits / 已知限制

- 离散 tick/event 播放，不是平滑动画
- 浏览器冒烟覆盖，非完整 E2E
- 无视觉回归
- 无 C# host / C# 宿主
- 无 Godot
- 阵型加成和羁绊逻辑已应用，但尚未进入 CI 流程与可玩发布闭环
- `opening_damage` / `formation_slots` 等字段在当前 phase 内未映射到可解释修正链路
- 无 generated artifact commit / 不提交生成文件
- `attack_interval_delta` 在 `synergy` 下当前仅在 `targeting/actions` schedule 初始化前更新；未做额外 DSL 扩展
- 目标选择解释还未作为独立 Phase 1 交付线收敛；当前仅在 `combat-behavior-pack` 中扩展 `attack` 与 `skill_trigger` 原因字段

## Recommended Next Branch / 推荐下一阶段分支

优先关注交付可展示闭环与交付稳定性：

1. `phase2/combat-behavior-pack`（若目标是提升战斗行为可解释性）
2. `phase2/ci-workflow`（若目标是稳定交付）
3. `phase1/viewer-polish`（若目标是演示稳定）
