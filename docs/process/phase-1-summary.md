# Phase 1 Summary / 第一阶段总结

## Phase 1 Completed Capabilities / 第一阶段已完成能力

- Deterministic pipeline from config / 配置到输出的确定性链路
- Python deterministic simulator / Python 确定性模拟器（`basic` 模式）
- Replay and report output / 回放与战报输出
- SVG Replay Viewer / SVG 回放调试器（read-only 本地回放查看）
- Formation bonus / 阵型加成（推荐规则）与 Synergy application / 羁绊应用（推荐规则）在 tick 0 一次性应用并可追踪
- Targeting explainability / 目标选择可解释性（`target_reason` / `target_score`）初步链路
- Combat System Pack / 战斗系统包 explainability（`status_apply`、`skill_cooldown`、`action_scheduled`、`victory_explanation`）
- Demo One-Click and Scenarios / 一键 Demo 与多场景（Scenario Manifest / 场景清单、Curated Fixtures / 固化样例数据、Scenario Selector / 场景选择器）
- Live Combat Runtime Foundation / 实时战斗运行时基础（BattleSession / 战斗会话、Step Runtime / 单步运行时、Battle Snapshot / 战斗状态快照、Event Buffer / 事件缓冲）
- Live Combat API / 实时战斗 API（Local HTTP Server / 本地 HTTP 服务、Battle Session Manager / 战斗会话管理器、start/step/snapshot/events/reset API）
- HTML Live Mode / HTML 实时模式（Live Combat API / 实时战斗 API 直连回放，定时调用 step 并消费 snapshot + events）
- Live Battle Visual Polish / 实时战斗视觉打磨（Battlefield-first layout / 战场优先布局、HP bar / 血条、行动条、攻击线、伤害跳字、胜负横幅）
- Live Pixi Battlefield Renderer / PixiJS 实时战场渲染器（PixiJS 主战场、DOM 阵容/战报/性能面板、视觉状态缓冲）
- Realtime Spatial Combat Foundation / 实时空间战斗基础（`spatial_combat.py` 空间模块、Continuous Position / 连续坐标、Movement Intent / 移动意图、Target Acquisition / 寻敌、Attack Range / 攻击范围、Unit Movement Event / 单位移动事件、report spatial counters / 战报空间计数）
- Browser Smoke Test / 浏览器冒烟测试（Playwright 基础检查）
- Verified real `demo_001` modifier evidence：
  - formation modifiers in report summary / 战报阵型修正数 > 0
  - synergy modifiers in report summary / 战报羁绊修正数 > 0
  - `stat_modifier` events with both `source_type=formation` and `source_type=synergy`
  - `status_apply` events for `shield_guard` and `banner_rally`
  - `skill_cooldown` events for successful skill use
  - `action_scheduled` events after actual unit actions
  - report `victory_explanation` derived from `battle_end`

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
- `phase2/combat-system-pack`: Combat System Pack / 战斗系统包 (current / pending review)
- `phase2/demo-one-click-and-scenarios`: Demo One-Click and Scenarios / 一键 Demo 与多场景 (current / pending review)
- `phase2/live-combat-runtime-foundation`: Live Combat Runtime Foundation / 实时战斗运行时基础 (current / pending review)
- `phase2/live-combat-api`: Live Combat API / 实时战斗 API (current / pending review)
- `phase2/html-live-mode`: HTML Live Mode / HTML 实时模式 (current / pending review)
- `phase2/live-battle-visual-polish`: Live Battle Visual Polish / 实时战斗视觉打磨 (merged / completed)
- `phase2/live-pixi-battlefield-renderer`: Live Pixi Battlefield Renderer / PixiJS 实时战场渲染器 (current / pending review)
- `phase2/realtime-spatial-combat-foundation`: Realtime Spatial Combat Foundation / 实时空间战斗基础 (current / pending review)
- `phase2/combat-architecture-formalization`: Combat Architecture Formalization / 战斗架构正式化 (current / pending review)
- `phase2/formation-and-engagement-system`: Formation and Engagement System / 编队与接敌系统 (current / pending review)
- `phase2/action-pipeline-migration`: Action Pipeline Migration / 行动管线迁移 (current)

## Current Commands / 当前命令

```bash
python tools/export_xlsx_to_json.py --input config/source --output config/generated
python tools/validate_config.py --input config/generated
python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003
python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples
python tools/run_live_api_smoke.py --config config/generated --battle demo_001 --seed 1001
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

提交的演示样例产物（用于 One-click Demo / 一键 Demo）：

- `web-viewer/public/samples/manifest.json`
- `web-viewer/public/samples/demo_001/replay.json`
- `web-viewer/public/samples/demo_001/battle_report.json`
- `web-viewer/public/samples/demo_seed_1002/replay.json`
- `web-viewer/public/samples/demo_seed_1002/battle_report.json`
- `web-viewer/public/samples/demo_seed_1003/replay.json`
- `web-viewer/public/samples/demo_seed_1003/battle_report.json`

运行时 API 产物（代码接口，不是文件产物）：

- `BattleSession / 战斗会话`
- `step_battle_session / 单步推进`
- `build_battle_snapshot / 构建战斗状态快照`
- `get_events_since / 读取事件缓冲`
- `Live Combat API / 实时战斗 API`
- `HTML Live Mode / HTML 实时模式`
- `BattleSessionManager / 战斗会话管理器`
- `tools/run_live_api.py`
- `tools/smoke_live_api.py`
- `tools/run_live_api_smoke.py`

## Known Limits / 已知限制

- 离散 tick/event 播放，不是平滑动画
- 浏览器冒烟覆盖，非完整 E2E
- 无视觉回归
- 无 Scenario Comparison / 场景对比 side-by-side UI（当前只提供场景选择和静态样例）
- Live Combat API / 实时战斗 API 仅提供本地 HTTP JSON 契约，不是产品化 live viewer
- 无 WebSocket
- `HTML live mode / HTML 实时模式` 已支持浏览器端手动接入 API 播放，仍有功能收口空间（如状态历史持久化、历史重放与并发会话展示）
- 无 C# host / C# 宿主
- 无 Godot
- 阵型加成和羁绊逻辑已应用，但尚未进入 CI 流程与可玩发布闭环
- `opening_damage` / `formation_slots` 等字段在当前 phase 内未映射到可解释修正链路
- 无 generated artifact commit / 不提交生成文件
- `attack_interval_delta` 在 `synergy` 下当前仅在 `targeting/actions` schedule 初始化前更新；未做额外 DSL 扩展
- 目标选择解释还未作为独立 Phase 1 交付线收敛；当前仅在 `combat-behavior-pack` 中扩展 `attack` 与 `skill_trigger` 原因字段
- 可视化仍偏调试风格，当前无复杂动画与高级回放特效

## Recommended Next Branch / 推荐下一阶段分支

优先关注交付可展示闭环与交付稳定性：

1. `phase2/combat-architecture-formalization`（若目标是先把运行时架构正式化，再继续迁移）
2. `phase2/combat-behavior-pack`（若目标是提升战斗行为可解释性）
3. `phase2/combat-system-pack`（若目标是状态、冷却、行动时间线和胜负解释可见性）
4. `phase2/demo-one-click-and-scenarios`（若目标是降低演示和冒烟门槛）
5. `phase2/live-combat-runtime-foundation`（若目标是从 replay 生成迈向可 step 的可移植运行时）
6. `phase2/live-combat-api`（若目标是向外部客户端暴露本地 HTTP API）
7. `phase2/live-battle-visual-polish`（若目标是提升展示观感）
8. `phase2/ci-workflow`（若目标是稳定交付）
9. `phase1/viewer-polish`（若目标是演示稳定）
10. `phase2/action-pipeline-migration`（若目标是把攻击/技能/效果结算统一迁移到 Action Pipeline / 行动管线）
