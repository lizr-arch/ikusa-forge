# Formation and Engagement System / 编队与接敌系统 Spec

## Why

当前战斗系统是"单兵直线接近最近敌人"。每个单位独立朝最近的敌人生成直线移动，没有编队协同、前后排职责、近战锁定、远程保持距离等战术行为。升级为"编队推进 + 接敌关系 + 前后排职责"是 Phase 2 战术深度的第一步。

## What Changes

- **新增** Formation System / 编队系统 (`formation_system.py`)：编队锚点（Formation Anchor / 编队锚点）、编队推进（Group Advance / 编队推进）、阵营中心（Side Centroid / 阵营中心）
- **新增** Engagement System / 接敌系统 (`engagement_system.py`)：接敌配对（Engagement Pairing / 接敌配对）、近战接敌锁定（Melee Engagement Lock / 近战接敌锁定）、远程保持距离（Ranged Hold Distance / 远程保持距离）、前排保护（Frontline Protection / 前排保护）
- **修改** `runtime_models.py`：新增编队/接敌字段到 `UnitState`
- **修改** `spatial_combat.py`：改造空间推进逻辑，引入编队 + 接敌系统
- **修改** `battle_session.py`：snapshot 包含新字段
- **修改** `report.py`：summary 和 per-unit 计数增加编队/接敌统计
- **修改** `replayTypes.ts`：新增事件类型和字段类型
- **修改** `replayState.ts`：`VisualUnit` 增加编队/接敌字段，处理新事件
- **修改** `livePixiBattlefieldRenderer.ts`：PixiJS 可选显示编队锚点、接敌关系线、远程保持距离圈
- **修改** `formationRosterView.ts`：阵容显示接敌角色、接敌目标、期望距离
- **修改** viewer smoke test：新 e2e 检查
- **新增** `test_formation_engagement.py`：编队/接敌单元测试
- **修改** `smoke_phase1_mvp.py`：新增编队/接敌冒烟检查
- **新增** `docs/process/formation-and-engagement-system-v0.1.md`
- **修改** README.md、combat-architecture doc、spatial-combat doc、phase-1-summary doc

## Impact

- Affected specs: spatial-combat-foundation, combat-architecture-formalization, live-pixi-battlefield-renderer
- Affected code:
  - Python: `runtime_models.py`, `spatial_combat.py`, `battle_session.py`, `report.py`, new `formation_system.py`, new `engagement_system.py`
  - Web: `replayTypes.ts`, `replayState.ts`, `livePixiBattlefieldRenderer.ts`, `formationRosterView.ts`, `viewer-smoke.spec.ts`
  - Tools: `smoke_phase1_mvp.py`, `smoke_demo_scenarios.py`
  - Docs: new process doc, updates to README and existing docs

## ADDED Requirements

### Requirement: Formation Anchor / 编队锚点

The system SHALL assign each unit a formation anchor position derived from the initial encounter grid layout and the unit's side, maintaining a group-level formation structure throughout the battle.

#### Scenario: Anchors assigned at init
- **WHEN** a battle session is initialized
- **THEN** every alive unit has `formation_anchor_x` and `formation_anchor_y` set
- **AND** units on the same side share the same `formation_group_id`

#### Scenario: Anchors update during group advance
- **WHEN** the battle progresses and a side's centroid moves toward the enemy
- **THEN** formation anchors shift proportionally to maintain relative positions within the group

#### Scenario: Anchor event emitted on change
- **WHEN** an anchor position changes significantly (change > 10% of the battlefield width, or every 10 ticks)
- **THEN** a `formation_anchor_update` event is emitted with the unit, new anchor, group_id, and reason

### Requirement: Group Advance / 编队推进

The system SHALL move units toward the enemy side as a group, preserving relative spacing within the formation, rather than having each unit independently dash to the nearest enemy.

#### Scenario: Friendlies maintain relative spacing
- **WHEN** a group advances over multiple ticks
- **THEN** no two friendly units overlap (distance < separation_radius)
- **AND** the overall formation shape is preserved relative to the centroid

#### Scenario: Units prefer anchor over nearest enemy
- **WHEN** a unit is not engaged with an enemy
- **THEN** the unit moves toward its formation anchor instead of directly toward the nearest enemy

### Requirement: Engagement Pairing / 接敌配对

The system SHALL assign each unit an engagement target based on role-based rules (frontline, ranged, support, flanker) and lock melee units to their target.

#### Scenario: Melee engagement lock
- **WHEN** a frontline unit enters attack range of an enemy
- **THEN** that enemy is set as `engagement_target` and locked
- **AND** the unit will not switch to a closer enemy while the current target is alive

#### Scenario: Melee engagement release on target death
- **WHEN** the locked engagement target dies
- **THEN** an `engagement_release` event is emitted
- **AND** the unit may select a new engagement target

#### Scenario: Ranged hold distance
- **WHEN** a ranged unit has an engagement target within attack range
- **THEN** the unit stops at `desired_distance` (approximately attack_range * 0.65)
- **AND** does not continue closing to melee range

#### Scenario: Support unit stays near anchor
- **WHEN** a support/banner unit is not directly engaged
- **THEN** the unit prefers to stay near its formation anchor
- **AND** does not rush to the frontline

### Requirement: Separation / 单位分离

The system SHALL apply lightweight separation to prevent friendly units from overlapping, without implementing a physics engine.

#### Scenario: Overlapping friendlies are pushed apart
- **WHEN** two friendly units are closer than `separation_radius`
- **THEN** they are pushed apart in opposite directions by a small amount per tick
- **AND** the push is proportional to the overlap

#### Scenario: Deterministic separation order
- **WHEN** separation is applied
- **THEN** the processing order is stable (sorted by instance_id)
- **AND** same seed produces the same result

### Requirement: Formation/Engagement Events

The system SHALL emit new event types for formation and engagement state changes.

#### Scenario: Engagement lock event
- **WHEN** a melee unit locks onto an engagement target
- **THEN** an `engagement_lock` event is emitted with unit, target, role, distance, reason

#### Scenario: Engagement release event
- **WHEN** a unit releases its engagement target
- **THEN** an `engagement_release` event is emitted with unit, target, reason

#### Scenario: Ranged hold event
- **WHEN** a ranged unit holds at desired distance
- **THEN** a `ranged_hold` event is emitted with unit, target, distance, desired_distance, reason

### Requirement: Snapshot Fields

The system SHALL include formation/engagement fields in unit snapshots.

#### Scenario: Snapshot includes new fields
- **WHEN** `build_battle_snapshot` is called
- **THEN** each unit's snapshot includes `formation_anchor_x`, `formation_anchor_y`, `formation_group_id`, `engagement_target`, `engagement_role`, `desired_distance`, `separation_radius`
- **AND** existing fields are preserved

### Requirement: Report Counters

The system SHALL track formation and engagement statistics in battle reports.

#### Scenario: Summary counters
- **WHEN** a battle report is generated
- **THEN** the summary includes `total_formation_anchor_updates`, `total_engagement_locks`, `total_engagement_releases`, `total_ranged_holds`

#### Scenario: Per-unit counters
- **WHEN** a battle report is generated
- **THEN** each unit report includes `formation_anchor_updates`, `engagement_locks`, `engagement_releases`, `ranged_holds`

### Requirement: PixiJS Visual Indicators

The PixiJS renderer SHALL support optional visual indicators for formation anchors, engagement locks, and ranged hold distances, with a toggle for debug layers.

#### Scenario: Default clean view
- **WHEN** the battlefield is rendered with default settings
- **THEN** no formation anchor dots or engagement lines are shown
- **AND** the canvas remains visually clean

#### Scenario: Debug toggle shows overlays
- **WHEN** the debug toggle is enabled
- **THEN** formation anchor dots appear for each unit
- **AND** engagement lock lines connect pairs
- **AND** ranged hold circles show desired distance

### Requirement: Formation Roster Fields

The formation roster SHALL display engagement role, engagement target, desired distance, and formation group ID.

#### Scenario: Roster shows engagement fields
- **WHEN** the formation roster is rendered
- **THEN** each unit row shows engagement role
- **AND** each unit row shows engagement target (or "-" if none)

### Requirement: Viewer Smoke Updates

The Playwright e2e tests SHALL verify formation/engagement features while keeping existing tests passing.

#### Scenario: Existing e2e tests pass
- **WHEN** `npm run test:e2e` is executed
- **THEN** all 4 existing tests pass unchanged

#### Scenario: Formation roster shows engagement role
- **WHEN** the viewer loads a battle with formation/engagement data
- **THEN** Formation Roster contains engagement role fields

#### Scenario: Unit detail shows formation/engagement
- **WHEN** a unit is clicked
- **THEN** Unit Detail shows Formation Anchor, Engagement Target, Engagement Role, Desired Distance

### Requirement: Determinism

The formation and engagement system SHALL be deterministic.

#### Scenario: Same seed produces identical event stream
- **WHEN** two battles are run with the same seed
- **THEN** the event streams (including new formation/engagement events) are identical

### Requirement: Not in Scope

The following SHALL NOT be implemented:
- A* pathfinding
- navmesh
- terrain
- obstacle collision
- morale system
- cavalry charge
- Godot / C# host
- WebSocket
- Phaser
- Live API response shape changes
- PixiJS renderer removal
- Python combat rules in TypeScript

## REMOVED Requirements

*None.*
