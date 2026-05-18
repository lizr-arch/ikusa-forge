# Fix Pixi Renderer Polish Spec

## Why
PR #24 introduced PixiJS battlefield renderer with several minor issues found during Web GPT code review: wrong attack line source field, missing action bar graphics, wrong status_expire detection, insufficient test assertions, and unclear PR boundary wording.

## What Changes
- Fix attack line to use `event.payload.attacker` with `event.payload.source` fallback
- Add real action bar (Graphics bg + fill) to Pixi unit sprites, leveraging existing `actionIndicatorRatio()`
- Fix status_expire detection from `event.payload.type` to `event.type`
- Update Playwright smoke test with Pixi canvas + live step performance assertions
- Update PR #24 body to clarify frontend framework boundaries

## Impact
- Affected specs: livePixiBattlefieldRenderer, viewer-smoke-e2e
- Affected code: `web-viewer/src/livePixiBattlefieldRenderer.ts`, `web-viewer/tests/viewer-smoke.spec.ts`
- No changes to Python battle rules, Live API response shape, or any other system

## ADDED Requirements

### Requirement: Attack line uses correct attacker field
The system SHALL draw attack lines using `event.payload.attacker` as primary source, falling back to `event.payload.source` for backward compatibility.

#### Scenario: Normal attack event draws attack line
- **WHEN** a ReplayEvent with `type === "attack"` and `payload.attacker === "ally_001"` is processed
- **THEN** an attack line SHALL be drawn from ally_001 to the target unit

#### Scenario: Legacy attack event with source field
- **WHEN** a ReplayEvent with `type === "attack"` has `payload.source` but no `payload.attacker`
- **THEN** the attack line SHALL still be drawn using `payload.source`

### Requirement: Pixi action bar renders below HP bar
The system SHALL render a subtle action bar (background + fill) below the HP bar on each unit sprite, using `actionIndicatorRatio()` to determine fill width.

#### Scenario: Unit with action progress
- **WHEN** a unit has `nextActionTick` and `actionIntervalTicks` set
- **THEN** the action bar SHALL show proportional fill based on `actionIndicatorRatio(unit)`

#### Scenario: Dead unit action bar
- **WHEN** a unit is dead (`alive === false`)
- **THEN** the action bar SHALL appear as empty (ratio 0) or greyed out

### Requirement: status_expire uses event.type
The system SHALL distinguish between status_apply and status_expire using `event.type` rather than `event.payload.type`.

#### Scenario: status_apply shows S+ badge
- **WHEN** a ReplayEvent with `event.type === "status_apply"` is processed
- **THEN** a "S+" badge SHALL be displayed

#### Scenario: status_expire shows SE badge
- **WHEN** a ReplayEvent with `event.type === "status_expire"` is processed
- **THEN** an "SE" badge SHALL be displayed

## MODIFIED Requirements

### Requirement: Playwright smoke test covers Pixi live mode
The existing viewer-smoke.spec.ts SHALL be extended with assertions that:
- Pixi canvas exists after live mode starts
- Performance panel remains visible after live steps
- Keep existing 4 tests passing

### Requirement: PR #24 body clarifies framework boundaries
The PR body SHALL be updated via `gh pr edit` to replace "no new frontend framework" with explicit:
- no React / Vue / Phaser
- PixiJS added only as battlefield renderer
- DOM debug panels preserved
And add Visual behavior notes about Pixi action bar and attack line fix.
