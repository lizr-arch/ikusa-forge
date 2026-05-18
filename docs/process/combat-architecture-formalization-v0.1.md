# Combat Architecture Formalization / 战斗架构正式化 v0.1

## Goal / 目标

本阶段把 Realtime Spatial Combat / 实时空间战斗 的 runtime 从“已经能跑”整理成“可长期演进”的正式架构。

重点不是增加新玩法，而是把 BattleSession / 战斗会话、Unit FSM / 单位状态机、Decision Models / 决策模型、Action Pipeline / 行动管线 和 Event/Snapshot Contract / 事件与快照契约 拆清楚。

## What changed / 本阶段做了什么

- 抽出了 `sim-python/ikusa_sim/unit_fsm.py`
- 新增 `UnitCombatState / 单位战斗状态`
- 新增 `sim-python/ikusa_sim/decisions.py`
- 新增 `sim-python/ikusa_sim/actions.py`
- `spatial_combat.py` 开始显式驱动 `moving_to_engage / engaged / dead`
- `battle_session.py` 的 snapshot / 状态快照 现在包含 `combat_state`
- `unit_spawn` payload / 单位生成事件载荷 现在也携带 `combat_state`
- HTML viewer / HTML 查看器 轻量展示 `Combat State（战斗状态）`

## Migration path / 迁移路线

后续战斗架构会按更细的阶段继续收口：

- `phase2/formation-and-engagement-system`
- `phase2/combat-action-pipeline`
- `phase2/status-lifecycle-system`
- `phase2/godot-adapter`

这几个阶段的目标不是立刻换引擎，而是让 runtime contract / 运行时契约 足够稳定，后续迁移时只替换消费端，不重写规则核心。

## Runtime behavior / 运行时行为

- `winner / reason / end_tick` 保持与当前 demo 基线一致
- `events / 事件流` 保持 deterministic / 确定性
- `combat_state` 进入 snapshot / 状态快照 和 `unit_spawn` / 单位生成事件
- `BattleSession / 战斗会话` 仍只负责编排，不持有复杂规则实现

## Not in Scope / 不在范围

- no behavior tree yet / 暂不引入行为树
- no full action pipeline migration yet / 暂不把所有战斗规则一次性迁入行动管线
- no C# host / 不做 C# 宿主
- no Godot / 不做 Godot
- no new combat rules / 不新增战斗规则
- no A* pathfinding / 不做 A* 寻路
- no navmesh / 不做导航网格
- no terrain / 不做地形
- no obstacle collision / 不做障碍物碰撞
