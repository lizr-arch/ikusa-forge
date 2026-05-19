# Formation and Engagement System / 编队与接敌系统 v0.1

## Goal / 目标

把当前"单兵直线接近最近敌人"升级为"编队推进 + 接敌关系 + 前后排职责"。

本阶段不做 A*寻路、navmesh、地形、障碍物碰撞，而是先把战术职责和团队行为建立起来。

## Formation Anchor / 编队锚点

Formation Anchor（编队锚点）是从初始 encounter grid（遭遇战格子配置）和 side（阵营）推导出的单位期望位置。

- 每个 side（阵营）有一个 Side Centroid（阵营中心），即存活单位的平均位置
- Group Advance（编队推进）让编队整体向敌人推进，锚点随之移动
- 单位优先向自己的 formation anchor（编队锚点）移动，而不是全部直接冲向最近敌人

## Group Advance / 编队推进

Group Advance（编队推进）让同一阵营的单位保持相对位置一起推进，而不是各自独立冲刺。

- 保持 Formation Cohesion（编队凝聚）：单位不应与编队锚点脱离太远
- Role-based Positioning（基于职责的站位）：不同职责的单位在编队中有不同位置

## Engagement Pairing / 接敌配对

Engagement Pairing（接敌配对）根据单位职责（frontline / ranged / support / flanker）分配接敌目标。

- Melee Engagement Lock（近战接敌锁定）：近战单位进入攻击范围后锁定目标，目标死亡后才重新选择
- Ranged Hold Distance（远程保持距离）：远程单位在 desired_distance 处停住，不贴脸冲锋
- Frontline Protection（前排保护）：前排单位优先接敌，保护后排

## Ranged Hold Distance / 远程保持距离

远程单位（弓兵等）不应冲到近战距离。它们在 desired_distance ≈ attack_range * 0.65 处停住，保持安全距离射击。

如果敌人靠得太近，远程单位可略微后撤一小段距离。

## Separation / 单位分离

Separation（单位分离）是轻量避免重叠机制，不是物理碰撞。

- 如果两个同阵营单位距离 < separation_radius，则沿相反方向推开一点
- 不做物理引擎，不做障碍物碰撞

## Event Contract / 事件契约

新增事件类型：

- `formation_anchor_update`（编队锚点更新）：锚点变化时发出，节流（每 10 tick 或显著变化）
- `engagement_lock`（接敌锁定）：近战单位锁定目标
- `engagement_release`（接敌解除）：目标死亡后释放
- `ranged_hold`（远程保持距离）：远程单位在期望距离停住

## Not in Scope / 不在范围

- A* pathfinding / A* 寻路
- navmesh / 导航网格
- terrain / 地形
- obstacle collision / 障碍物碰撞
- morale / 士气
- cavalry charge / 骑兵冲锋
- Godot / C# host
- WebSocket
- Phaser
- 战斗规则写到 TypeScript 里
