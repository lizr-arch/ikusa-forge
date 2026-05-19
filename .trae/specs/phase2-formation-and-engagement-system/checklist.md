# Checklist

## Runtime Model
- [ ] `UnitState` has `formation_anchor_x: float`, `formation_anchor_y: float`, `formation_group_id: str`
- [ ] `UnitState` has `engagement_target: Optional[str]`, `engagement_role: str`, `desired_distance: float`, `separation_radius: float`
- [ ] Default `formation_group_id` is unit's `side`
- [ ] `engagement_role` defaults derived correctly: vanguard/front/shield/spear/katana → `frontline`, bow/archer → `ranged`, banner/support → `support`, ninja → `flanker`
- [ ] `desired_distance` defaults derived correctly from role and attack_range
- [ ] `separation_radius` defaults to `radius * 1.8`
- [ ] Existing fields `position_x/y`, `engaged_target`, `movement_intent` preserved

## Formation System
- [ ] `formation_system.py` exists with all required functions
- [ ] `initialize_formation_anchors` sets anchors from grid layout + side centroid
- [ ] `update_formation_anchors` advances groups toward enemy centroid
- [ ] `formation_anchor_update` events emitted (throttled: every 10 ticks or significant change)
- [ ] No pathfinding, no terrain, no obstacle logic

## Engagement System
- [ ] `engagement_system.py` exists with all required functions
- [ ] `update_engagement_pairs` drives per-tick engagement decisions
- [ ] `choose_engagement_target` role-aware target selection
- [ ] Melee units lock engagement target when entering attack range
- [ ] Melee units release engagement target on target death
- [ ] Ranged units hold at desired_distance, do not close to melee
- [ ] Support units stay near anchor
- [ ] `engagement_lock`, `engagement_release`, `ranged_hold` events emitted

## Spatial Integration
- [ ] `spatial_combat.py` calls formation_system and engagement_system in correct order
- [ ] Frontline: move toward anchor before engagement, stay at melee when engaged
- [ ] Ranged: move toward desired_distance, stop when there
- [ ] Support: move toward formation anchor
- [ ] Separation: friendly units pushed apart when closer than separation_radius
- [ ] Attack gating preserved: no attack outside attack_range
- [ ] Deterministic sorting maintains reproducibility

## Snapshot
- [ ] `build_battle_snapshot` includes `formation_anchor_x`, `formation_anchor_y`, `formation_group_id`
- [ ] `build_battle_snapshot` includes `engagement_target`, `engagement_role`, `desired_distance`, `separation_radius`
- [ ] Old snapshot fields preserved

## Report
- [ ] Summary includes `total_formation_anchor_updates`, `total_engagement_locks`, `total_engagement_releases`, `total_ranged_holds`
- [ ] Per-unit includes `formation_anchor_updates`, `engagement_locks`, `engagement_releases`, `ranged_holds`

## Python Tests
- [ ] `test_formation_engagement.py` exists
- [ ] Test A: formation anchors assigned at init
- [ ] Test B: group advance preserves relative spacing (no overlap)
- [ ] Test C: melee engagement lock (lock, no swap while target alive, release on death)
- [ ] Test D: ranged hold distance (bow doesn't close to melee, stays near desired_distance)
- [ ] Test E: support anchor (banner/support stays near anchor)
- [ ] Test F: deterministic event stream with same seed
- [ ] Test G: snapshot includes formation/engagement fields

## TypeScript Types
- [ ] `KnownReplayEventType` includes `formation_anchor_update`, `engagement_lock`, `engagement_release`, `ranged_hold`
- [ ] `UnitSnapshot` includes new formation/engagement fields
- [ ] `LiveUnitSnapshot` includes new formation/engagement fields
- [ ] `ReportSummary` includes new counters
- [ ] `UnitReport` includes new counters

## VisualState
- [ ] `VisualUnit` has `formationAnchorX`, `formationAnchorY`, `formationGroupId`, `engagementTarget`, `engagementRole`, `desiredDistance`, `separationRadius`
- [ ] `applyEvent` handles `formation_anchor_update`, `engagement_lock`, `engagement_release`, `ranged_hold`
- [ ] `applyUnitSpawn` reads new snapshot fields
- [ ] `buildLiveUnit` reads new snapshot fields

## PixiJS Viewer
- [ ] Debug toggle exists (checkbox or button)
- [ ] Debug off: clean battlefield, no anchor dots or engagement lines
- [ ] Debug on: formation anchor dots visible
- [ ] Debug on: engagement lock lines visible
- [ ] Debug on: ranged hold circles visible
- [ ] PixiJS canvas still renders units correctly

## Formation Roster
- [ ] Roster shows `engagement_role`
- [ ] Roster shows `engagement_target` (or "-" if none)
- [ ] Roster shows `desired_distance`
- [ ] Roster shows `formation_group_id`

## Viewer Smoke (e2e)
- [ ] All existing 4 e2e tests pass
- [ ] Formation roster contains engagement role fields
- [ ] Unit detail shows Formation Anchor after clicking
- [ ] Unit detail shows Engagement Target after clicking
- [ ] Unit detail shows Desired Distance after clicking
- [ ] Timeline can show engagement_lock or formation_anchor_update
- [ ] Pixi canvas visible in live mode test

## Smoke Tools
- [ ] `smoke_phase1_mvp.py`: `formation_anchor_update > 0`
- [ ] `smoke_phase1_mvp.py`: `engagement_lock > 0`
- [ ] `smoke_phase1_mvp.py`: `ranged_hold >= 0`
- [ ] `smoke_phase1_mvp.py`: report counters equal replay event counts
- [ ] `smoke_phase1_mvp.py`: at least one unit has `engagement_locks > 0`
- [ ] `smoke_phase1_mvp.py`: snapshot or replay has `engagement_role`
- [ ] `smoke_demo_scenarios.py`: curated scenarios pass

## Documentation
- [ ] `docs/process/formation-and-engagement-system-v0.1.md` created with Chinese term explanations
- [ ] README.md updated
- [ ] `docs/architecture/combat-architecture-v0.1.md` updated
- [ ] `docs/process/realtime-spatial-combat-foundation-v0.1.md` updated
- [ ] `docs/process/phase-1-summary.md` updated

## Full Pipeline
- [ ] `export_xlsx_to_json` succeeds
- [ ] `validate_config` succeeds
- [ ] `run_demo_battle` succeeds, winner is `ally`, reason is `enemy_eliminated`
- [ ] `smoke_phase1_mvp` succeeds
- [ ] `generate_demo_scenarios` succeeds
- [ ] `smoke_demo_scenarios` succeeds
- [ ] `run_live_api_smoke` succeeds
- [ ] `python -m unittest discover -s sim-python/tests` passes all tests
- [ ] `npm run typecheck` succeeds
- [ ] `npm run build` succeeds
- [ ] `npm run test:e2e` passes all tests
- [ ] `git diff --exit-code -- web-viewer/public/samples` clean
- [ ] `git diff --check` clean
- [ ] `git diff --cached --check` clean

## PR
- [ ] Branch `phase2/formation-and-engagement-system` pushed
- [ ] Normal PR created to `main` (not draft)
- [ ] PR body includes Summary, Verification, Gameplay behavior changed, Boundary sections
- [ ] PR not merged
