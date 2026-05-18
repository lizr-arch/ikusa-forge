# Live Viewer Performance Pass / 实时回放性能修复 v0.1

## Goal / 目标

Live Battle / 实时战斗 已经能连上 Live Combat API / 实时战斗 API 并展示连续空间战斗，但 live step / 实时推进 在事件较多时会明显变卡。

本阶段把 HTML Live Mode / HTML 实时模式 的目标从“能看见数据”提升到“可测量地接近/稳定 30 FPS”，让本地 demo_001 在默认情况下保持可玩和可调试。

本阶段只做 HTML Live Mode / HTML 实时模式 的性能修复，不改战斗规则，不改 Python runtime / Python 运行时 行为，不改变 demo 胜负结果。

## Frame Budget / 帧预算

30 FPS / 每秒 30 帧 意味着单帧预算大约是 33.3ms。

本阶段的性能目标不是“每次 API step / 接口推进 都重绘整页”，而是：

- 保持渲染循环 / Render Loop 轻量
- 把 heavy DOM 重建限制在 state change / 状态变化 时
- 通过 Performance（性能） 遥测观察 FPS / 帧率、Frame Time / 帧耗时、P95 Frame / P95 帧耗时

## Root Cause / 根因

此前 live step / 实时推进 走的是 full render / 全量渲染 路径，导致每次 step 都重复重建：

- Board / 战场 SVG
- Timeline / 时间线 全部 rows
- Scenario controls / 场景控制项
- Report / 战报 与 Scenario Summary / 场景摘要
- Unit Detail / 单位详情

当 live event / 实时事件 数量上升时，DOM 重建成本会直接压低帧率。

## Fix / 修复

本阶段引入了这些改动：

- API step loop / 接口推进循环 和 requestAnimationFrame render loop / requestAnimationFrame 渲染循环 解耦
- `renderLiveFrame / 实时帧渲染`
- capped live timeline / 限制实时时间线行数
- scenario controls memo / 场景控制缓存
- reduced report rerender / 降低战报重绘频率
- performance telemetry / 性能观测
- board static layer caching / 战场静态层缓存

具体行为：

- live step / 实时单步 只更新必要的 live frame / 实时帧 区域
- renderLiveFrame / 实时帧渲染 以 30 FPS 左右的频率运行，但只有在状态变化时才重绘重型区域
- Timeline / 时间线 默认只显示最新 100 条事件
- Report / 战报 在 live battle in progress / 实时战斗进行中 时只保留轻量提示，战斗结束后再刷新胜负结果
- Scenario controls / 场景控制 不再每帧重建
- Performance（性能） 区块显示：
  - FPS（帧率）
  - Frame Time（帧耗时）
  - Avg Frame（平均帧耗时）
  - P95 Frame（P95 帧耗时）
  - Step API（接口推进）
  - Render（渲染）
  - Board（战场）
  - Timeline（时间线）
  - Timeline Rows（事件行数）
  - Total Events（总事件）

## Not in Scope / 不在范围

- No combat rule changes / 不改战斗规则
- No Python runtime behavior changes / 不改 Python 运行时行为
- No WebSocket / 不做 WebSocket
- No new frontend framework / 不引入新前端框架
- No visual regression / 不做视觉回归截图测试
