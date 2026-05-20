# Action Pipeline Migration / 行动管线迁移 v0.1

## Goal / 目标

本阶段把攻击/技能/效果结算迁移到 Action Pipeline / 行动管线。

当前 main 已具备 Action Pipeline skeleton / 行动管线骨架，但实际攻击/技能/伤害/状态/冷却/死亡结算还没有完全迁入。

本阶段把这些逻辑迁入 unified pipeline / 统一管线，不新增玩法也不改外部契约。

## Pipeline / 管线

五阶段设计：

```text
CombatAction / 战斗行动
  → Validate / 行动验证（检查存活/范围/冷却/战斗未结束）
  → Resolve / 行动结算（计算伤害和效果）
  → ApplyEffects / 应用效果（修改 UnitState）
  → EmitEvents / 发出事件（统一输出 battle events）
```

## Internal Only / 内部实现

Action Pipeline 是 runtime 内部结构，不改变 replay schema / 回放 schema。

所有事件类型和 payload 字段保持不变。

## Basic Attack Migration / 普攻迁移

`battle_session.py` 中的 `_apply_basic_attack` 现在通过 `run_combat_action` 执行，保持事件顺序不变。

## Skill Action Migration / 技能迁移

`skills.py` 中的技能结算逻辑现在通过 `run_combat_action` 执行，保持事件顺序不变。

技能选择逻辑（`get_ready_skills`）保持不变。

## Completion Status / 收口状态

本阶段后续收口把“散落手工路径”继续迁入管线：

- `_emit_action_scheduled` 及直接 `_run_tick` 调度写入 -> `ActionScheduleEffect`
- `try_use_on_battle_start_skills`、`try_use_on_attacked_skills`、`try_use_on_ally_attacked_skills` -> `run_combat_action`
- 状态过期事件 -> `status_system.py` + `StatusExpireEffect` + `status_expire`

Legacy helper（`_emit_skill_trigger` / `_apply_status` / `_mark_skill_used_and_emit_cooldown`）仍保留注释为 fallback，作为集成路径的兼容兜底，不作为主流程入口。

## Effect Models / 效果模型

新增的 6 个 Effect dataclass：

- DamageEffect / 伤害效果
- StatusApplyEffect / 状态效果
- CooldownEffect / 冷却效果
- DeathEffect / 死亡效果
- ActionScheduleEffect / 行动安排效果
- StatusExpireEffect / 状态过期效果

## Event Contract Preservation / 事件契约保持

保留的所有事件类型：

- `unit_spawn`
- `unit_death`
- `attack`
- `skill_trigger`
- `damage`
- `status_apply`
- `skill_cooldown`
- `action_scheduled`
- `battle_end`
- `stat_modifier`
- `unit_move`
- `status_expire`

## Not in Scope / 不在范围

- 不新增技能
- 不做行为树
- 不做 Godot/C#
- 不做地形/寻路
- 不改 Live API shape
- 不改 replay schema
