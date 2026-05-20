# Action Pipeline Migration / 行动管线迁移 Spec

## Why

当前 `actions.py` 仅有骨架（`CombatAction` / `ActionResult`），而实际的攻击/技能/伤害/死亡/冷却/行动安排逻辑散落在 `battle_session.py`、`skills.py` 和 `combat_rules.py` 中。本阶段把这些结算逻辑迁移到统一的 Action Pipeline / 行动管线内部，不改变外部事件契约与 demo 结果。

## What Changes

- 扩展 `actions.py`：`CombatAction` 增加 `skill_id`、`metadata` 字段；`ActionResult` 增加 `effects` 字段
- 新增 `effect_models.py`：`DamageEffect`、`StatusApplyEffect`、`CooldownEffect`、`DeathEffect`、`ActionScheduleEffect` 数据类
- 新增 `action_pipeline.py`：统一的 `run_combat_action` 管线（Validate → Resolve → ApplyEffects → EmitEvents）
- 迁移 `battle_session.py` 中的 `_apply_basic_attack` 逻辑进管线
- 迁移 `skills.py` 中的技能结算逻辑（`_resolve_damage_skill`、`_apply_status`、`_mark_skill_used_and_emit_cooldown`）进管线
- 保持所有现有事件类型及其 payload 字段不变
- 保持 `demo_001` winner/reason/end_tick 稳定
- 新增测试 `test_action_pipeline.py`
- 新增文档 `docs/process/action-pipeline-migration-v0.1.md`

## Impact

- Affected specs: combat-architecture-formalization, formation-and-engagement-system
- Affected code:
  - `sim-python/ikusa_sim/actions.py` — 扩展
  - `sim-python/ikusa_sim/effect_models.py` — 新增
  - `sim-python/ikusa_sim/action_pipeline.py` — 新增
  - `sim-python/ikusa_sim/battle_session.py` — 修改（_apply_basic_attack 内部逻辑迁移）
  - `sim-python/ikusa_sim/skills.py` — 修改（skill resolve 逻辑迁移）
  - `sim-python/tests/test_action_pipeline.py` — 新增
  - `README.md` — 更新
  - `docs/architecture/combat-architecture-v0.1.md` — 更新
  - `docs/process/combat-architecture-formalization-v0.1.md` — 更新
  - `docs/process/phase-1-summary.md` — 更新
  - `docs/process/action-pipeline-migration-v0.1.md` — 新增

## ADDED Requirements

### Requirement: Effect Models / 效果模型数据类

系统 SHALL 提供以下 dataclass，均可 JSON-safe 转换：

- `DamageEffect`：source、target、amount、reason
- `StatusApplyEffect`：source、target、status_id、stat、amount、expire_tick、reason
- `CooldownEffect`：source、skill_id、start_tick、ready_tick、cooldown_ticks
- `DeathEffect`：unit、reason
- `ActionScheduleEffect`：unit、current_tick、next_action_tick、action_interval_ticks、reason

#### Scenario: All effect types are JSON-serializable
- **WHEN** any effect dataclass is converted via `dataclasses.asdict`
- **THEN** `json.dumps` succeeds without error

### Requirement: Action Pipeline / 行动管线

系统 SHALL 提供 `run_combat_action(state, action, tick, events)` 函数，按以下阶段执行：

1. **Validate** / 行动验证：检查单位存活、目标存活、范围、冷却、战斗未结束
2. **Resolve** / 行动结算：计算伤害和效果
3. **ApplyEffects** / 应用效果：修改 UnitState (hp、状态、冷却、死亡、行动安排)
4. **EmitEvents** / 发出事件：生成 BattleEvent 追加到 events 列表

#### Scenario: Basic attack through pipeline
- **WHEN** 构造 BasicAttackAction 并调用 run_combat_action
- **THEN** 生成 attack event、damage event，target hp 减少

#### Scenario: Out-of-range validation
- **WHEN** target 不在 attack_range 内
- **THEN** action 验证失败，不产生 damage

#### Scenario: Dead unit validation
- **WHEN** attacker 已死亡
- **THEN** action 验证失败

#### Scenario: Battle finished validation
- **WHEN** battle 已结束
- **THEN** action 验证失败

### Requirement: Basic Attack Migration / 普攻迁移

`battle_session.py` 中的 `_apply_basic_attack` 内部逻辑 SHALL 迁移为通过 `run_combat_action` 调用，保持事件顺序：attack → damage → death (if needed) → action_scheduled (if applicable)

#### Scenario: Basic attack preserves event contract
- **WHEN** demo_001 中发生普攻
- **THEN** attack 事件 payload 保持 `attacker`、`target`、`target_reason`、`target_score` 字段

### Requirement: Skill Action Migration / 技能迁移

`skills.py` 中的技能结算逻辑 SHALL 通过 `run_combat_action` 调用，保持事件顺序：skill_trigger → damage/status_apply → skill_cooldown → death (if needed) → action_scheduled (if applicable)

#### Scenario: Skill action preserves event contract
- **WHEN** demo_001 中发生技能触发
- **THEN** `skill_trigger` 事件 payload 保持 `source`、`skill`、`trigger`、`targets`、`target_reason`、`target_score` 字段
- **THEN** `skill_cooldown` 事件 payload 保持 `source`、`skill`、`start_tick`、`ready_tick`、`cooldown_ticks` 字段

### Requirement: Event Contract Preservation / 事件契约保持

系统 SHALL 不删除、不重命名任何现有事件类型：attack、skill_trigger、damage、death、status_apply、status_expire、skill_cooldown、action_scheduled、unit_move、target_acquired、enter_range、engage_start、formation_anchor_update、engagement_lock、engagement_release、ranged_hold、battle_start、battle_end、unit_spawn、stat_modifier

#### Scenario: All event types remain
- **WHEN** 运行 demo_001 seed=1001
- **THEN** 所有上述事件类型仍然存在于事件流中

### Requirement: Demo Stability / Demo 稳定性

系统 SHALL 保持 `demo_001` seed=1001 的 winner/reason/end_tick 不变。
- winner: "ally"
- reason: "enemy_eliminated"
- end_tick: 458

#### Scenario: Demo result unchanged
- **WHEN** 运行 run_basic_combat(bundle, "demo_001", 1001)
- **THEN** state.result.winner == "ally", state.result.reason == "enemy_eliminated", state.result.end_tick == 458

## MODIFIED Requirements

### Requirement: CombatAction / 战斗行动 (扩展)

`CombatAction` dataclass SHALL 增加以下可选字段：
- `skill_id: Optional[str]` — 技能 ID（skill action 时使用）
- `metadata: Dict[str, object]` — 附加元数据

### Requirement: ActionResult / 行动结果 (扩展)

`ActionResult` dataclass SHALL 增加以下字段：
- `effects: List[EffectUnion]` — 本行动产生的效果列表

## REMOVED Requirements

无。Action Pipeline 是内部实现重构，不删除任何外部可观察行为。
