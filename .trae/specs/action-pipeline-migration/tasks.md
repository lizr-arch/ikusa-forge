# Tasks

- [ ] Task 1: Extend Action models / 扩展行动模型
  - [ ] 1.1 扩展 `CombatAction` dataclass：增加 `skill_id`、`metadata` 字段
  - [ ] 1.2 扩展 `ActionResult` dataclass：增加 `effects` 字段
  - [ ] 1.3 更新 `build_basic_attack_action` 和 `build_skill_action` 签名以适配新字段
  - [ ] 1.4 验证：现有 `test_combat_architecture.py` 测试通过

- [ ] Task 2: Add Effect Models / 新增效果模型
  - [ ] 2.1 创建 `sim-python/ikusa_sim/effect_models.py`
  - [ ] 2.2 实现 `DamageEffect`、`StatusApplyEffect`、`CooldownEffect`、`DeathEffect`、`ActionScheduleEffect` dataclass
  - [ ] 2.3 确保所有 dataclass 可 JSON-safe 转换
  - [ ] 2.4 验证：`test_action_pipeline.py` 中 JSON-safe 测试通过

- [ ] Task 3: Add Action Pipeline / 新增行动管线
  - [ ] 3.1 创建 `sim-python/ikusa_sim/action_pipeline.py`
  - [ ] 3.2 实现 `build_basic_attack_action(state, attacker, target, tick)`
  - [ ] 3.3 实现 `build_skill_action(state, source, skill, targets, tick)`
  - [ ] 3.4 实现 `validate_combat_action(state, action)`（含单位存活、目标存活、范围、冷却、战斗结束检查）
  - [ ] 3.5 实现 `resolve_combat_action(state, action)`（普攻→DamageEffect，技能→DamageEffect/StatusApplyEffect）
  - [ ] 3.6 实现 `apply_effects(state, effects, tick, events)`
  - [ ] 3.7 实现 `emit_events_from_effects(state, action, effects, tick, events)`
  - [ ] 3.8 实现 `run_combat_action(state, action, tick, events)`
  - [ ] 3.9 验证：`test_action_pipeline.py` 中 pipeline 流程测试通过

- [ ] Task 4: Migrate Basic Attack / 迁移普攻
  - [ ] 4.1 将 `battle_session.py` 中 `_apply_basic_attack` 内部逻辑改为调用 `run_combat_action`
  - [ ] 4.2 保持 attack → damage → death → action_scheduled 事件顺序不变
  - [ ] 4.3 保持 attack/damage/death/action_scheduled payload 字段不变
  - [ ] 4.4 验证：`test_basic_combat.py` 全部通过

- [ ] Task 5: Migrate Skill Action / 迁移技能行动
  - [ ] 5.1 将 `skills.py` 中 `_resolve_damage_skill` 内部逻辑改为调用 `run_combat_action`
  - [ ] 5.2 将 `skills.py` 中 `_apply_status` 和 `_mark_skill_used_and_emit_cooldown` 调用迁入管线
  - [ ] 5.3 保持 skill_trigger → damage/status_apply → skill_cooldown → death → action_scheduled 事件顺序
  - [ ] 5.4 保持 skill_trigger/damage/status_apply/skill_cooldown payload 字段不变
  - [ ] 5.5 验证：`test_skill_combat.py` 全部通过

- [ ] Task 6: Add Tests / 新增测试
  - [ ] 6.1 创建 `sim-python/tests/test_action_pipeline.py`
  - [ ] 6.2 覆盖：basic attack action build + validate + run
  - [ ] 6.3 覆盖：out-of-range validation
  - [ ] 6.4 覆盖：skill action 产生 skill_trigger + damage + skill_cooldown
  - [ ] 6.5 覆盖：death effect（damage 后 hp <= 0，unit.alive = False）
  - [ ] 6.6 覆盖：action_scheduled event 字段
  - [ ] 6.7 覆盖：JSON-safe 转换
  - [ ] 6.8 覆盖：demo_001 stability（winner/reason/end_tick）

- [ ] Task 7: Add Docs / 新增文档
  - [ ] 7.1 创建 `docs/process/action-pipeline-migration-v0.1.md`
  - [ ] 7.2 更新 `README.md`（添加 Phase 2 Action Pipeline 条目）
  - [ ] 7.3 更新 `docs/architecture/combat-architecture-v0.1.md`（标记 Action Pipeline migration phase 完成）
  - [ ] 7.4 更新 `docs/process/combat-architecture-formalization-v0.1.md`（标记 Action Pipeline migration phase 开始）
  - [ ] 7.5 更新 `docs/process/phase-1-summary.md`（添加 Action Pipeline Migration PR）

- [ ] Task 8: Full Verification / 全面验证
  - [ ] 8.1 运行全部 Python 测试：`python -m unittest discover -s sim-python/tests`
  - [ ] 8.2 运行 demo battle：`python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic`
  - [ ] 8.3 运行 smoke：`python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001`
  - [ ] 8.4 生成 demo scenarios：`python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003`
  - [ ] 8.5 运行 scenario smoke：`python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples`
  - [ ] 8.6 运行 live API smoke：`python tools/run_live_api_smoke.py --config config/generated --battle demo_001 --seed 1001`
  - [ ] 8.7 运行 web-viewer typecheck：`cd web-viewer && npm install && npm run typecheck`
  - [ ] 8.8 运行 web-viewer build：`npm run build`
  - [ ] 8.9 运行 web-viewer e2e：`npm run test:e2e`
  - [ ] 8.10 Fixture consistency：`git diff --exit-code -- web-viewer/public/samples`
  - [ ] 8.11 Diff checks：`git diff --check` 和 `git diff --cached --check`

- [ ] Task 9: Commit, Push, Create PR / 提交推送创建 PR
  - [ ] 9.1 `git add .`
  - [ ] 9.2 `git commit -m "feat(sim): migrate combat actions to pipeline"`
  - [ ] 9.3 `git push -u origin phase2/action-pipeline-migration`
  - [ ] 9.4 创建普通 PR（base: main, head: phase2/action-pipeline-migration）
  - [ ] 9.5 PR body 包含完整 Summary / Verification / Runtime behavior / Boundary 说明

# Task Dependencies

- Task 2 depends on Task 1 (effect models reference CombatAction/ActionResult)
- Task 3 depends on Task 1, Task 2 (pipeline uses effects and actions)
- Task 4 depends on Task 3 (migration uses pipeline)
- Task 5 depends on Task 3 (migration uses pipeline)
- Task 6 depends on Task 4, Task 5 (tests verify migrated behavior)
- Task 7 can run parallel to Task 1-6
- Task 8 depends on Task 1-7
- Task 9 depends on Task 8
