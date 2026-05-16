# Browser Smoke Test / 浏览器冒烟测试 v0.1

This stage adds a minimal Browser Smoke Test / 浏览器冒烟测试 for the SVG Replay Viewer / SVG 回放调试器.

It turns the existing Manual Smoke / 手动冒烟 checklist into a small Playwright / 浏览器自动化测试工具 check. It is not a complete E2E / 端到端测试 system.

## Goal / 目标

The goal is to verify the current Viewer Contract / 回放器契约 in a Headless Browser / 无头浏览器:

- the viewer opens,
- File Input Loading / 文件输入加载 works for `replay.json / 回放 JSON` and `battle_report.json / 战报 JSON`,
- core UI surfaces are populated from generated artifacts / 生成产物.

This test does not change combat behavior / 战斗行为 and does not add viewer features / 回放器功能.

## Scope / 范围

Smoke Coverage / 冒烟覆盖范围:

- replay/report loading / 回放与战报加载.
- board / 棋盘.
- timeline / 时间线.
- unit detail / 单位详情.
- playback controls / 播放控制.
- report panel / 战报面板.

## Not in Scope / 不在范围

Not covered:

- visual regression / 视觉回归.
- pixel checks / 像素检查.
- screenshot baseline / 截图基准测试.
- cross-browser matrix / 跨浏览器矩阵.
- large E2E matrix / 大型端到端测试矩阵.
- combat logic changes / 战斗逻辑修改.
- viewer feature expansion / 回放器功能扩展.
- backend server / 后端服务.

## Implementation / 实现

Files:

- `web-viewer/playwright.config.ts`: Playwright / 浏览器自动化测试工具 config.
- `web-viewer/tests/viewer-smoke.spec.ts`: Browser Smoke Test / 浏览器冒烟测试.

The Playwright config / Playwright 配置:

- starts Vite / Vite 开发服务器 automatically through `webServer`.
- uses only a Chromium project / Chromium 项目.
- uses `baseURL=http://127.0.0.1:5173`.
- disables screenshot / 截图, trace / 跟踪, and video / 视频 capture.
- does not depend on external network during test execution / 测试执行不依赖外部网络.

## Commands / 命令

Generate demo artifacts / 生成演示产物:

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
```

Install and run browser smoke / 安装并运行浏览器冒烟:

```bash
cd web-viewer
npm install
npx playwright install chromium
npm run test:e2e
```

Optional headed run / 可选有界面运行:

```bash
npm run test:e2e:headed
```

## Expected Result / 预期结果

`npm run test:e2e` should:

1. start Vite / 启动 Vite.
2. open the viewer in Chromium / 在 Chromium 中打开回放器.
3. load `../runs/demo_001/replay.json`.
4. load `../runs/demo_001/battle_report.json`.
5. verify the status / 状态, metadata / 元数据, board / 棋盘, timeline / 时间线, unit detail / 单位详情, playback controls / 播放控制, and report panel / 战报面板.

## Known Limitations / 已知限制

- The test requires generated demo artifacts / 生成演示产物 before running.
- It is a smoke test / 冒烟测试, not a full E2E / 端到端测试 suite.
- It does not test visual layout quality / 视觉布局质量.
- It does not test every browser / 不测试所有浏览器.
- It does not prove final demo readiness / 不证明最终演示就绪.
