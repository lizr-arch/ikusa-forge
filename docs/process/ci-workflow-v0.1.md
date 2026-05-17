# CI Workflow / CI 流水线 v0.1

## Goal / 目标

把当前可交付能力的验证闭环固定为主干门禁（Main Gate / 主干门禁），而不是新增战斗逻辑或玩法。

目标是保证主干每次变更都通过：

- 配置导出与校验
- demo 运行
- 静态 MVP 冒烟
- Python 单测
- Web 回放器 Typecheck / Build / 浏览器冒烟

## Jobs / 作业

### Python simulator / Python 模拟器 (python-sim)

该 job 只验证 Python 验收链：

- `checkout`
- `python 3.11` + `python --version`
- `tools/export_xlsx_to_json.py`
- `tools/validate_config.py`
- `tools/run_demo_battle.py`
- `tools/smoke_phase1_mvp.py`
- `python -m unittest discover -s sim-python/tests`

### Web viewer / Web 回放器 (web-viewer)

该 job 先复用同一组 demo 验证产物，再验证 Web:

- `checkout`
- `python 3.11` + `node`
- `tools/export_xlsx_to_json.py`
- `tools/validate_config.py`
- `tools/run_demo_battle.py`
- `tools/smoke_phase1_mvp.py`
- `npm install`（当前 CI 为了稳定性使用 npm install）
- `npm ci` 为理想目标：当前平台可选依赖 lockfile 仍存在差异，暂不稳定
- `npm run typecheck`
- `npm run build`
- `npx playwright install chromium --with-deps`
- `npm run test:e2e`

## Commands / 命令

CI 中实际执行的命令如下（按 job 顺序）：

### Python job / Python 作业

```bash
python --version
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
python -m unittest discover -s sim-python/tests
```

### Web viewer job / Web 回放器作业

```bash
python --version
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001

cd web-viewer
npm install
npm run typecheck
npm run build
npx playwright install chromium --with-deps
npm run test:e2e
```

## Generated Artifacts / 生成产物

以下目录/文件在 CI 中会被生成，但不提交到仓库：

- `config/generated/`
- `runs/demo_001/`
- `web-viewer/dist/`
- `web-viewer/test-results/`（Playwright 运行输出）

## Browser Smoke / 浏览器冒烟

CI 的浏览器冒烟只跑 Chromium，一点说明：

- 不做跨浏览器矩阵（Cross-browser matrix / 跨浏览器矩阵）
- 不做视觉回归（Visual Regression / 视觉回归）
- 不做截图对比（Screenshot / 截图）断言
- 不依赖外部网络

## Known Limits / 已知限制

- CI 不覆盖 C# host / C# 宿主
- CI 不覆盖 Godot
- CI 不覆盖完整视觉验收
- CI 不证明完整产品可玩链路（只保护 MVP 验证链）
- CI 不做 xlsx adapter / xlsx 适配器
- CI 不改变战斗逻辑，不改 viewer 功能，不引入新框架
