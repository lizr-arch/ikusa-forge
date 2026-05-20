## Summary

Adds Action Pipeline Migration / 行动管线迁移:
- **CombatAction / 战斗行动** — 扩展 `skill_id`、`metadata` 字段成为攻击与技能结算统一入口
- **ValidateAction / 行动验证** — 状态感知验证（单位存活、目标存活、攻击范围、技能冷却、战斗未结束）
- **ResolveAction / 行动结算** — 通过 metadata 驱动产生 DamageEffect / StatusApplyEffect / CooldownEffect
- **ApplyEffects / 应用效果** — 修改 UnitState（hp、状态、冷却、死亡）
- **EmitEvents / 发出事件** — 统一输出 battle events，保持事件契约不变
- **Basic Attack Migration / 普攻迁移** — `battle_session._apply_basic_attack` 通过 `run_combat_action` 执行
- **Skill Action Migration / 技能迁移** — `skills.py` 的 `_resolve_damage_skill`、`_handle_guard`、`_handle_banner_rally` 通过 `run_combat_action` 执行
- **Event contract preserved / 事件契约保持** — 所有 11 种事件类型及其 payload 字段不变

### actions.py vs action_pipeline.py

- `actions.py` provides **CombatAction / ActionResult data models**, `build_basic_attack_action` / `build_skill_action` build helpers, and backward-compatible skeleton helpers (`validate_combat_action` / `resolve_combat_action`) that remain available but are not used by the live runtime.
- `action_pipeline.py` is the **actual state-aware runtime pipeline** (`validate_combat_action` / `resolve_combat_action` / `apply_effects` / `emit_events_from_effects` / `run_combat_action`) used by `battle_session.py` and `skills.py`.

### New files

| File | Purpose |
|------|---------|
| `sim-python/ikusa_sim/effect_models.py` | 5 个 Effect dataclass（DamageEffect, StatusApplyEffect, CooldownEffect, DeathEffect, ActionScheduleEffect） |
| `sim-python/ikusa_sim/action_pipeline.py` | 核心管线：Validate → Resolve → ApplyEffects → EmitEvents |
| `sim-python/tests/test_action_pipeline.py` | 7 个测试场景覆盖 |
| `docs/process/action-pipeline-migration-v0.1.md` | 过程文档 |

### Modified files

| File | Change |
|------|--------|
| `sim-python/ikusa_sim/actions.py` | `CombatAction` + `skill_id`/`metadata`，`ActionResult` + `effects` |
| `sim-python/ikusa_sim/battle_session.py` | `_apply_basic_attack` 改用 `run_combat_action` |
| `sim-python/ikusa_sim/skills.py` | `_resolve_damage_skill`/`_handle_guard`/`_handle_banner_rally` 改用 pipeline；`_mark_skill_used_and_emit_cooldown` / `_apply_status` / `_emit_skill_trigger` 保留供 `try_use_on_battle_start_skills` / `try_use_on_attacked_skills` / `try_use_on_ally_attacked_skills` 使用 |
| `README.md` | 添加 Action Pipeline Migration 条目 |
| `docs/architecture/combat-architecture-v0.1.md` | Migration path 更新 |
| `docs/process/combat-architecture-formalization-v0.1.md` | Migration path 更新 |
| `docs/process/phase-1-summary.md` | 添加 PR 和 Recommended Next Branch |

## Verification

```
# Python: 139 tests passed
python -m unittest discover -s sim-python/tests -v
→ Ran 139 tests in 188.136s — OK

# Smoke: all passed
python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001
→ Phase 1 MVP smoke passed

# Scenario smoke: 3/3 passed
python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples
→ Demo scenario smoke passed

# Live API smoke: passed
python tools/run_live_api_smoke.py --config config/generated --battle demo_001 --seed 1001
→ Live API smoke passed

# Web viewer: all passed
npm run typecheck → passed
npm run build → passed
npm run test:e2e → 4 passed (14.2s)

# Fixture consistency
git diff --exit-code -- web-viewer/public/samples → clean
git diff --check → clean
git diff --cached --check → clean
```

## Runtime behavior

- **demo_001** winner="ally", reason="enemy_eliminated", end_tick=458 — 不变
- **events 数量**: 1670（不变）
- **attack/damage/skill/death/cooldown/action_scheduled** 事件 payload 字段完全保持
- **Live API response shape** 不变
- **PixiJS viewer** 正常渲染
- **Determinism**: 同一 config+battle+seed 产生完全一致的事件流

### Known limitations

- **ActionScheduleEffect / 行动调度效果** exists and is tested in `test_action_pipeline.py`.
- However, the integrated battle-session scheduling path still updates `next_action_tick` and emits `action_scheduled` in `battle_session.py` for now.
- Full action schedule migration is intentionally deferred to a later pipeline hardening step.
- `skills.py` retains `_emit_skill_trigger` / `_apply_status` / `_mark_skill_used_and_emit_cooldown` for `try_use_on_battle_start_skills` / `try_use_on_attacked_skills` / `try_use_on_ally_attacked_skills` — these on-battle-start and on-attacked paths wil be migrated in a future PR.

## Boundary

- no new skills
- no config schema change
- no Live API response shape change
- no PixiJS renderer removed
- no Phaser introduced
- no Godot/C# code
- no terrain/pathfinding
- no morale/cavalry charge
- no combat rules moved to TypeScript
- no AI strategy major changes
- no replay schema change (Action Pipeline is internal-only)
