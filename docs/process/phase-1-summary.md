# Phase 1 Summary / 第一阶段总结

## Phase 1 Completed Capabilities / 第一阶段已完成能力

- Deterministic pipeline from config / 配置到输出的确定性链路
- Python deterministic simulator / Python 确定性模拟器（`basic` 模式）
- Replay and report output / 回放与战报输出
- SVG Replay Viewer / SVG 回放调试器（read-only 本地回放查看）
- Browser Smoke Test / 浏览器冒烟测试（Playwright 基础检查）

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
- 无羁绊/阵型加成逻辑
- 无 generated artifact commit / 不提交生成文件

## Recommended Next Branch / 推荐下一阶段分支

优先关注交付可展示闭环与交付稳定性：

1. `phase1/phase1-demo-package`（本文档对应）
2. 视团队目标决定下一步：`phase1/viewer-polish` 或 `phase1/ci-hardening` 或 `phase1/formation-bonus`
