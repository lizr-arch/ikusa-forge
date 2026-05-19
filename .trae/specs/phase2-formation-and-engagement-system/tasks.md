# Tasks

## 1. Runtime Model / 运行时模型更新
- [ ] Task 1: Add formation/engagement fields to `UnitState` in `runtime_models.py`
  - Add fields: `formation_anchor_x`, `formation_anchor_y`, `formation_group_id`, `engagement_target`, `engagement_role`, `desired_distance`, `separation_radius`
  - Apply default values based on role: front roles → `frontline`, bow/archer → `ranged`, banner/support → `support`, ninja → `flanker`
  - Derive `desired_distance` from attack_range per role type
  - Set `separation_radius = radius * 1.8`
  - Rename `engaged_target` usage to emphasize it is the *combat* engaged target (keep field, add `engagement_target` as new field)
  - Ensure existing fields (`position_x/y`, `engaged_target`, `movement_intent`) are NOT deleted
  - Update snapshot in `battle_session.py` to include all new fields

## 2. Formation System / 编队系统
- [ ] Task 2: Create `formation_system.py` with formation anchor and group advance logic
  - `initialize_formation_anchors(state)`: derive initial anchors from encounter grid mapping + side centroid
  - `update_formation_anchors(state, tick)`: advance groups toward enemy centroid
  - `formation_anchor_for_unit(unit, state)`: return current anchor for a unit
  - `formation_cohesion_score(unit)`: measure how far a unit is from its anchor
  - `side_centroid(state, side)`: compute avg position of alive units on a side
  - Emit `formation_anchor_update` events throttled (every 10 ticks or on significant change)
  - No complex pathfinding, no terrain/obstacle logic

## 3. Engagement System / 接敌系统
- [ ] Task 3: Create `engagement_system.py` with pairing, lock, hold, and role-based logic
  - `update_engagement_pairs(state, events, tick)`: main entry point for engagement decisions
  - `choose_engagement_target(unit, enemies)`: select target by role
  - `lock_melee_engagement(unit, target)`: lock frontline melee to target
  - `should_hold_ranged_distance(unit, target)`: check if ranged unit should stop
  - `desired_engagement_distance(unit, target)`: compute target distance for role
  - Frontline: lock target when in attack range, release on death
  - Ranged: hold at desired_distance, don't close to melee range
  - Support: prefer anchor proximity unless engaged
  - Flanker: v1 uses same logic as frontline but with distinct role
  - Emit `engagement_lock`, `engagement_release`, `ranged_hold` events

## 4. Spatial Integration / 空间系统接入
- [ ] Task 4: Refactor `spatial_combat.py` to integrate formation and engagement systems
  - In `update_spatial_engagements`: call formation anchor update, then engagement update, then generate movement decisions per role
  - Frontline: if not engaged, move toward formation anchor / engagement target; if engaged, stay at melee range
  - Ranged: move toward desired_distance; stop when at distance; optional light retreat if too close
  - Support: move toward formation anchor
  - Flanker: v1 moves toward engagement target
  - Apply lightweight separation: if two same-side units closer than separation_radius, push apart slightly
  - Preserve attack gating: no attack outside attack_range
  - Maintain deterministic stable sort by instance_id

## 5. Report Updates / 战报更新
- [ ] Task 5: Update `report.py` with formation and engagement counters
  - Summary: `total_formation_anchor_updates`, `total_engagement_locks`, `total_engagement_releases`, `total_ranged_holds`
  - Per-unit: `formation_anchor_updates`, `engagement_locks`, `engagement_releases`, `ranged_holds`

## 6. Smoke Tool Updates / 冒烟工具更新
- [ ] Task 6: Update `smoke_phase1_mvp.py` with formation/engagement checks
  - Check `formation_anchor_update > 0`
  - Check `engagement_lock > 0`
  - Check `ranged_hold >= 0`
  - Verify report summary counters match replay event counts
  - Verify at least one unit has `engagement_locks > 0`
  - Verify snapshot or replay contains `engagement_role`
  - Update expected `end_tick` and event count if they change
  - Winner/reason should remain `ally` / `enemy_eliminated`

- [ ] Task 7: Update `smoke_demo_scenarios.py` to ensure curated scenarios still pass

## 7. Tests / 测试
- [ ] Task 8: Create `test_formation_engagement.py` with comprehensive test coverage
  - Test A: formation anchors assigned at init
  - Test B: group advance preserves relative spacing
  - Test C: melee engagement lock and release on death
  - Test D: ranged hold distance
  - Test E: support unit stays near anchor
  - Test F: deterministic event stream with same seed
  - Test G: snapshot includes formation/engagement fields

## 8. TypeScript Type Updates / TypeScript 类型更新
- [ ] Task 9: Update `replayTypes.ts` with new event types and fields
  - Add event types: `formation_anchor_update`, `engagement_lock`, `engagement_release`, `ranged_hold`
  - Add snapshot fields: `formation_anchor_x`, `formation_anchor_y`, `formation_group_id`, `engagement_target`, `engagement_role`, `desired_distance`, `separation_radius`
  - Add report summary fields: `total_formation_anchor_updates`, `total_engagement_locks`, `total_engagement_releases`, `total_ranged_holds`
  - Add unit report fields: `formation_anchor_updates`, `engagement_locks`, `engagement_releases`, `ranged_holds`

## 9. VisualState Updates / 视觉状态更新
- [ ] Task 10: Update `replayState.ts` to handle new events and fields
  - Add fields to `VisualUnit`: `formationAnchorX`, `formationAnchorY`, `formationGroupId`, `engagementTarget`, `engagementRole`, `desiredDistance`, `separationRadius`
  - Add event handlers in `applyEvent`: handle `formation_anchor_update`, `engagement_lock`, `engagement_release`, `ranged_hold`
  - Update `applyUnitSpawn` to read new snapshot fields
  - Update `buildLiveUnit` to read new snapshot fields

## 10. PixiJS Viewer Updates / PixiJS 展示更新
- [ ] Task 11: Update `livePixiBattlefieldRenderer.ts` with optional debug overlays
  - Add debug toggle mechanism (checkbox/DOM element or internal flag)
  - When debug enabled: draw formation anchor dots (small circles at anchor positions)
  - When debug enabled: draw engagement lock lines between paired units
  - When debug enabled: draw ranged hold circles at desired_distance radius
  - When debug disabled: keep clean battlefield view
  - Add `setDebugOverlay(enabled: boolean)` to renderer interface

## 11. Formation Roster Updates / 阵容视图更新
- [ ] Task 12: Update `formationRosterView.ts` to show engagement fields
  - Show `engagement_role` (engagementRole) in roster rows
  - Show `engagement_target` (engagementTarget) or "-" in roster rows
  - Show `desired_distance` (desiredDistance) in roster rows
  - Show `formation_group_id` (formationGroupId) in roster rows

## 12. Viewer Smoke Updates / 冒烟测试更新
- [ ] Task 13: Update `viewer-smoke.spec.ts` with formation/engagement e2e checks
  - Verify formation roster contains engagement role fields
  - Verify unit detail shows Formation Anchor / Engagement Target / Engagement Role / Desired Distance after clicking
  - Verify Pixi canvas is still visible
  - Verify timeline can show engagement_lock or formation_anchor_update events
  - Ensure existing 4 e2e tests still pass

## 13. Documentation / 文档
- [ ] Task 14: Create `docs/process/formation-and-engagement-system-v0.1.md`
  - Include Goal / 目标, Formation Anchor / 编队锚点, Group Advance / 编队推进, Engagement Pairing / 接敌配对, Ranged Hold Distance / 远程保持距离, Separation / 单位分离, Event Contract / 事件契约, Not in Scope / 不在范围
  - All key English terms must have Chinese explanations in parentheses

- [ ] Task 15: Update existing docs
  - Update README.md to mention formation and engagement system
  - Update `docs/architecture/combat-architecture-v0.1.md` migration path
  - Update `docs/process/realtime-spatial-combat-foundation-v0.1.md`
  - Update `docs/process/phase-1-summary.md`

## 14. Verification / 验证
- [ ] Task 16: Run full Python verification pipeline
  - `python tools/export_xlsx_to_json.py --input config/source --output config/generated`
  - `python tools/validate_config.py --input config/generated`
  - `python tools/run_demo_battle.py --battle demo_001 --seed 1001 --config config/generated --out runs/demo_001 --mode basic`
  - `python tools/smoke_phase1_mvp.py --run runs/demo_001 --viewer web-viewer --battle demo_001 --seed 1001`
  - `python tools/generate_demo_scenarios.py --source config/source --out web-viewer/public/samples --battle demo_001 --seeds 1001 1002 1003`
  - `python tools/smoke_demo_scenarios.py --samples web-viewer/public/samples`
  - `python tools/run_live_api_smoke.py --config config/generated --battle demo_001 --seed 1001`
  - `python -m unittest discover -s sim-python/tests`

- [ ] Task 17: Run full Web verification pipeline
  - `cd web-viewer && npm install && npm run typecheck && npm run build && npm run test:e2e`
  - Verify `git diff --exit-code -- web-viewer/public/samples`
  - Verify `git diff --check`
  - Verify `git diff --cached --check`

## 15. Submit / 提交
- [ ] Task 18: Commit, push, and create PR
  - `git add .`
  - `git commit -m "feat(sim): add formation and engagement system"`
  - `git push -u origin phase2/formation-and-engagement-system`
  - Create normal PR to main with full body including Summary, Verification, Gameplay behavior changed, Boundary sections

# Task Dependencies
- Task 2 (formation_system.py) depends on Task 1 (runtime model fields)
- Task 3 (engagement_system.py) depends on Task 1 (runtime model fields)
- Task 4 (spatial_combat refactor) depends on Task 2 and Task 3
- Task 5 (report) depends on Task 2 and Task 3 (new event types)
- Task 6 (smoke) depends on Task 4 and Task 5
- Task 7 (tests) depends on Task 2, Task 3, Task 4
- Task 8 (replayTypes) can start in parallel with Python tasks
- Task 9 (replayState) depends on Task 8
- Task 10 (PixiJS) depends on Task 9
- Task 11 (formRoster) depends on Task 9
- Task 12 (viewer smoke) depends on Task 10 and Task 11
- Task 13 (docs) can start anytime
- Task 14 (verification Python) depends on Tasks 1-7
- Task 15 (verification Web) depends on Tasks 8-12
- Task 16 (submit) depends on Tasks 14 and 15
