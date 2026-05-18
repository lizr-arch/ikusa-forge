# Rebase PR #22 onto latest main Spec

## Why
PR #22 (`feat(sim): formalize combat architecture`) was branched from an older main before PR #24 (PixiJS live battlefield renderer) was squash-merged. The branch has drifted: it would delete PixiJS files if merged as-is. A rebase is needed to bring PR #22 up to date with latest main while preserving all PR #24 frontend work.

## What Changes
- Rebase `phase2/combat-architecture-formalization` onto `origin/main` (HEAD: c2eb055)
- During conflict resolution:
  - **Preserve** all PR #24 files: `livePixiBattlefieldRenderer.ts`, `visualStateBuffer.ts`, `formationRosterView.ts`, `troopVisualConfig.ts`, `performanceTelemetry.ts`, PixiJS-related changes in `main.ts`, `styles.css`, `index.html`, `package.json`
  - **Preserve** all PR #22 additions: `unit_fsm.py`, `decisions.py`, `actions.py`, `UnitState.combat_state`, combat_state in snapshot/unit_spawn, combat architecture docs, `test_combat_architecture.py`
  - **Merge** web-viewer files where both branches touch the same file (e.g., `replayState.ts`, `replayTypes.ts`, `timelineView.ts`, `unitDetailView.ts`, `boardView.ts`)
- Update PR #22 body to document rebase status and verification results
- Push with `--force-with-lease`

## Impact
- Affected specs: combat-architecture-formalization, live-pixi-battlefield-renderer
- Affected code: `sim-python/ikusa_sim/unit_fsm.py`, `sim-python/ikusa_sim/actions.py`, `sim-python/ikusa_sim/decisions.py`, `web-viewer/src/livePixiBattlefieldRenderer.ts`, `web-viewer/src/main.ts`, and all conflicting files
- No changes to Python battle rules, Live API response shape

## ADDED Requirements

### Requirement: Rebase preserves PixiJS live battlefield renderer
The system SHALL retain all PR #24 files after rebase, including `livePixiBattlefieldRenderer.ts`, `visualStateBuffer.ts`, `formationRosterView.ts`, `troopVisualConfig.ts`, `performanceTelemetry.ts`, and PixiJS canvas live mode in `main.ts`.

#### Scenario: PixiJS renderer file exists after rebase
- **WHEN** rebase completes
- **THEN** `web-viewer/src/livePixiBattlefieldRenderer.ts` SHALL exist and contain PixiJS rendering logic

#### Scenario: PixiJS dependencies remain in package.json
- **WHEN** rebase completes
- **THEN** `web-viewer/package.json` SHALL contain pixi.js dependency

### Requirement: Rebase preserves PR #22 combat architecture additions
The system SHALL retain all PR #22 Python additions after rebase, including `unit_fsm.py`, `decisions.py`, `actions.py`, `UnitState.combat_state`, and `test_combat_architecture.py`.

#### Scenario: unit_fsm.py exists after rebase
- **WHEN** rebase completes
- **THEN** `sim-python/ikusa_sim/unit_fsm.py` SHALL exist with FSM logic

#### Scenario: combat_state appears in unit_spawn
- **WHEN** a battle runs after rebase
- **THEN** `combat_state` field SHALL be present in `unit_spawn` events and snapshots

### Requirement: All verifications pass after rebase
The system SHALL pass all Python and web verification steps without regression.

#### Scenario: Python tests pass
- **WHEN** `python -m unittest discover -s sim-python/tests` runs
- **THEN** all tests SHALL pass including `test_combat_architecture.py`

#### Scenario: Web e2e tests pass
- **WHEN** `npm run test:e2e` runs
- **THEN** all Playwright tests SHALL pass, including PixiJS live mode assertions

#### Scenario: demo_001 output stable
- **WHEN** `run_demo_battle.py` runs with seed 1001
- **THEN** events count SHALL be 716, winner/reason/end_tick SHALL match known stable values

### Requirement: PR #22 body updated with rebase information
The PR #22 body SHALL be updated via `gh pr edit` to include rebase status, verification output, and boundary declarations.

#### Scenario: PR body contains rebase status
- **WHEN** `gh pr view 22 --json body` is queried after update
- **THEN** body SHALL contain "## Rebase status" section

## MODIFIED Requirements
None.

## REMOVED Requirements
None.
