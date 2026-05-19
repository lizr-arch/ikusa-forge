# Realtime Spatial Combat Foundation / 实时空间战斗基础 v0.1

## Goal / 目标

Realtime Spatial Combat / 实时空间战斗把 Ikusa Forge 从 Static Formation Legacy / 旧静态阵型 的站桩自动战斗推进到 Continuous Position / 连续坐标 战斗。

本阶段目标是让每个单位拥有 `position_x / position_y` 连续坐标、`move_speed` 移动速度、`attack_range` 攻击范围 和 Movement Intent / 移动意图。单位先通过 Target Acquisition / 寻敌 找到最近敌人，移动进入 Attack Range / 攻击范围 后才触发攻击、技能、伤害与死亡。

## Runtime Model / 运行时模型

`UnitState / 单位运行时状态` 新增空间字段：

- Continuous Position / 连续坐标: `position_x`, `position_y`
- Velocity / 速度: `velocity_x`, `velocity_y`
- Facing Angle / 朝向角: `facing_angle`
- Radius / 半径: `radius`
- Move Speed / 移动速度: `move_speed`
- Attack Range / 攻击范围: `attack_range`
- Engagement Range / 接敌范围: `engagement_range`
- Engaged Target / 接敌目标: `engaged_target`
- Movement Intent / 移动意图: `movement_intent`

初始空间布局仍来自 encounter grid / 遭遇战格子配置，但运行时会映射到 Continuous Position / 连续坐标：

```text
enemy side:
  y = 80 + row * 36
ally side:
  y = 320 + row * 36
x = 80 + col * 56
```

## Movement and Engagement / 移动与接敌

每个 tick 会先执行空间推进：

1. Target Acquisition / 寻敌：按欧氏距离选择最近存活敌人。
2. Movement Intent / 移动意图：如果目标超出 Attack Range / 攻击范围，则沿直线移动。
3. Enter Range Event / 进入射程事件：首次进入攻击范围时发出 `enter_range`。
4. Engage Start Event / 开始交战事件：首次可交战时发出 `engage_start`。
5. 攻击调度：只有 `engaged_target` 在 Attack Range / 攻击范围 内且 `next_action_tick` 到达时才攻击。

这是第一版 Simple Engagement / 简单接敌。它不是 A* pathfinding / A* 寻路，不包含 terrain / 地形、obstacle collision / 障碍物碰撞 或 complex physics / 复杂物理。

## Spatial Module / 空间模块

空间逻辑已经抽到 `sim-python/ikusa_sim/spatial_combat.py`，并由 `battle_session.py` 调用，便于后续继续扩展：

- `initialize_spatial_state`
- `update_spatial_engagements`
- `distance_between`
- `in_attack_range`
- `nearest_alive_enemy`
- `move_toward_target`
- `select_engaged_target_decision`

报表层同时新增空间计数：

- `total_unit_moves`
- `total_target_acquired`
- `total_enter_range`
- `total_engage_start`

以及 per-unit 计数：

- `moves`
- `target_acquired`
- `entered_range`
- `engagements_started`

## Event Contract / 事件契约

新增事件：

- Unit Movement Event / 单位移动事件: `unit_move`
- Target Acquisition / 寻敌事件: `target_acquired`
- Enter Range Event / 进入射程事件: `enter_range`
- Engage Start Event / 开始交战事件: `engage_start`

旧事件仍保留：

- `attack`
- `skill_trigger`
- `damage`
- `death`
- `action_scheduled`
- `battle_end`

因为攻击现在需要先移动进入范围，demo 的 event stream / 事件流发生预期变化：`unit_move` 等空间事件增加，`battle_end.end_tick` 从旧静态阵型的 tick 240 变为当前空间接敌后的 tick 341。胜负仍为 `ally / enemy_eliminated`。

## Snapshot / 状态快照

Battle Snapshot / 战斗状态快照 仍使用 `battle_snapshot.v0.1`，但每个 unit snapshot / 单位快照 附加空间字段：

- `position_x`, `position_y`
- `velocity_x`, `velocity_y`
- `facing_angle`
- `radius`
- `move_speed`
- `attack_range`
- `engagement_range`
- `engaged_target`
- `movement_intent`
- `combat_state` / 战斗状态（供 Unit FSM / 单位状态机 消费）

Live Combat API / 实时战斗 API 的 JSON response shape / JSON 响应形状 不变，客户端通过现有 `snapshot` 和 `events` 消费这些新增字段。

## HTML Live Mode / HTML 实时模式

HTML Live Mode / HTML 实时模式 现在使用 snapshot / 状态快照中的 Continuous Position / 连续坐标 渲染 Live Battlefield / 实时战场。单位会在战场中连续移动，进入 Attack Range / 攻击范围 后出现攻击线、伤害跳字、死亡标记和 Victory Banner / 胜负横幅。

Replay Mode / 回放模式 和 Scenario Mode / 场景模式 也可读取 `unit_move` 事件并重建移动后的显示状态。

## Not in Scope / 不在范围

本阶段不做：

- A* pathfinding / A* 寻路
- navmesh / 导航网格
- terrain / 地形
- obstacle collision / 障碍物碰撞
- cavalry charge / 骑兵冲锋
- morale / 士气
- complex physics / 复杂物理
- formation-level group steering / 阵型级群体导航（→ 正在 Phase 2 Formation and Engagement System / 编队与接敌系统中处理）
- C# host / C# 宿主
- Godot
- WebSocket
- new frontend framework / 新前端框架
- React / Vue / Phaser / PixiJS / Three.js
- visual regression / 视觉回归
- cross-browser matrix / 跨浏览器矩阵
