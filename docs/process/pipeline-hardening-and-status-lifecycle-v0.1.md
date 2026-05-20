# Pipeline Hardening and Status Lifecycle / 管线加固与状态生命周期 v0.1

## Goal / 目标

本阶段在 `Action Pipeline` 已有基础上，把剩余关键战斗路径也收口到统一管线：

- action_scheduled / 行动调度
- `battle_start` / 战斗开始技能
- `on_attacked` / 被攻击反应技能
- `on_ally_attacked` / 友军被攻击反应技能
- 状态生命周期（`status_apply`、`status_expire`）

目标是减少“散落逻辑”（integrated path 里手工更新）并保持事件契约不变，从而继续优化 runtime 可移植性与可测试性。

## Action Schedule Migration / 行动调度迁移

此前 `battle_session.py` 在集成路径里直接写 `next_action_tick` 并触发 `_emit_action_scheduled`。
现在已迁移为：

- `run_combat_action(..., schedule_next_action=True)` 产出 `ActionScheduleEffect`
- `apply_effects` 统一写 `unit.next_action_tick`
- `emit_events_from_effects` 统一发 `action_scheduled`

效果：

- 单元测试可覆盖完整链路（执行行动 → 产生 action_scheduled payload）
- `action_scheduled` payload 字段保持不变
- 事件顺序保持为 `attack/skill_trigger` 后接 `damage/status/cooldown/death`，再到 `action_scheduled`

## Reactive Skill Migration / 反应技能迁移

本阶段把以下技能入口迁移到 pipeline：

- `try_use_on_battle_start_skills`
- `try_use_on_attacked_skills`
- `try_use_on_ally_attacked_skills`
- `on_attack` 流中的主动技能（含主技能）

迁移方式是统一构造 `CombatAction`，走 `run_combat_action`，并通过 `ActionResult`、`Effect`、事件发射闭环处理：

- `skill_trigger` / 技能触发事件
- `damage` / 伤害
- `status_apply` / 状态应用
- `skill_cooldown` / 技能冷却
- `action_scheduled` / 行动调度（主动作业可选）

保留旧实现 helper 仅作为兼容回退，不作为集成主路径。

## Status Lifecycle / 状态生命周期

新增 `sim-python/ikusa_sim/status_system.py`，把状态应用与过期收口：

- `apply_status_effect`：应用状态并立即调整单位数值
- `build_status_expire_effects`：每 tick 构造 `StatusExpireEffect`（按单位 id + status id 稳定排序）
- `apply_status_expire_effect`：回滚 stat 并移除状态
- `expire_status_effects`：兼容性批量过期路径
- `emit_status_expire_event`：事件 payload 结构兼容

`battle_session.py` 在每 tick 调用过期检查并发出 `status_expire`，报告和测试通过 `total_status_expired`、单位 `statuses_expired` 打点观察。

## Event Contract Preservation / 事件契约保持

本阶段只改内部分发路径，`event type` / `payload field` 不变。重点保留：

- `action_scheduled` / 行动调度效果
- `skill_trigger` / 技能触发
- `status_apply` / 状态应用
- `status_expire` / 状态过期
- `skill_cooldown` / 技能冷却

## Not in Scope / 不在范围

- 不新增技能
- 不改配置 schema
- 不改 Live API shape / 不改 replay schema
- 不改 Python runtime 战斗规则本体（仅状态/事件路径收口）
- 不引入 Phaser / WebSocket / Godot / C#
- 不做地形 / 复杂寻路 / 障碍碰撞
- 不把规则迁移到 TypeScript
